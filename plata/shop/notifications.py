import StringIO

from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from pdfdocument.document import PDFDocument

import plata
from plata.reporting.order import invoice_pdf, packing_slip_pdf
from plata.shop import signals


class EmailHandler(object):
    def __init__(self, always_to=None, always_bcc=None):
        self.always_to = always_to
        self.always_bcc = always_bcc

    def __call__(self, sender, **kwargs):
        email = self.message(sender, **kwargs)

        if self.always_to:
            email.to += list(self.always_to)
        if self.always_bcc:
            email.bcc += list(self.always_bcc)

        email.send()

    def context(self, ctx, **kwargs):
        ctx.update({
            'site': Site.objects.get_current(),
            })
        ctx.update(kwargs)
        return ctx


class ContactCreatedHandler(EmailHandler):
    """
    Send an e-mail message to a newly created contact, optionally BCC'ing
    the addresses passed as ``always_bcc`` upon handler initialization.

    Usage::

        signals.contact_created.connect(
            ContactCreatedHandler(),
            weak=False)

    or::

        signals.contact_created.connect(
            ContactCreatedHandler(always_bcc=['owner@example.com']),
            weak=False)
    """

    def message(self, sender, contact, **kwargs):
        email = render_to_string('plata/notifications/contact_created.txt',
            self.context(kwargs)).splitlines()

        return EmailMessage(
            subject=email[0],
            body=u'\n'.join(email[2:]),
            to=[contact.user.email],
            )


class SendInvoiceHandler(EmailHandler):
    """
    Send an e-mail with attached invoice to the customer after successful
    order completion, optionally BCC'ing the addresses passed as ``always_bcc``
    to the handler upon initialization.

    Usage::

        signals.order_completed.connect(
            SendInvoiceHandler(always_bcc=['owner@example.com']),
            weak=False)
    """

    def message(self, sender, order, **kwargs):
        email = render_to_string('plata/notifications/order_completed.txt',
            self.context(kwargs)).splitlines()

        content = StringIO.StringIO()
        pdf = PDFDocument(content)
        invoice_pdf(pdf, order)

        message = EmailMessage(
            subject=email[0],
            body=u'\n'.join(email[2:]),
            to=[order.email],
            )

        message.attach('invoice-%09d.pdf' % order.id, content.getvalue(), 'application/pdf')
        return message


class SendPackingSlipHandler(EmailHandler):
    """
    Send an e-mail with attached packing slip to the addresses specified upon
    handler initialization. You should pass at least one address in either
    the ``always_to`` or the ``always_bcc`` argument, or else the e-mail
    will go nowhere.

    Usage::

        signals.order_completed.connect(
            SendPackingSlipHandler(always_to=['warehouse@example.com']),
            weak=False)
    """

    def message(self, sender, order, **kwargs):
        email = render_to_string('plata/notifications/packing_slip.txt',
            self.context(kwargs)).splitlines()

        content = StringIO.StringIO()
        pdf = PDFDocument(content)
        packing_slip_pdf(pdf, order)

        message = EmailMessage(
            subject=email[0],
            body=u'\n'.join(email[2:]),
            )
        message.attach('packing-slip-%09d.pdf' % order.id, content.getvalue(), 'application/pdf')
        return message


"""
signals.contact_created.connect(
    ContactCreatedHandler(always_bcc=plata.settings.PLATA_ALWAYS_BCC),
    weak=False)
signals.order_completed.connect(
    SendInvoiceHandler(always_bcc=plata.settings.PLATA_ALWAYS_BCC + plata.settings.PLATA_ORDER_BCC),
    weak=False)
signals.order_completed.connect(
    SendPackingSlipHandler(
        always_to=plata.settings.PLATA_SHIPPING_INFO,
        always_bcc=plata.settings.PLATA_ALWAYS_BCC + plata.settings.PLATA_ORDER_BCC)
    weak=False)
"""
