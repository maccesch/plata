import sys

from django.db import models
from django.utils.translation import ugettext_lazy as _

from plata.product.models import ProductBase, register_price_cache_handlers
from plata.shop.models import Price, PriceManager


class ProductPrice(Price):
    product = models.ForeignKey('product.Product', verbose_name=_('product'),
        related_name='prices')

    class Meta:
        app_label = 'product'
        get_latest_by = 'id'
        ordering = ['-valid_from']
        verbose_name = _('price')
        verbose_name_plural = _('prices')

    objects = PriceManager()

register_price_cache_handlers(ProductPrice)


class Product(ProductBase):
    """(Nearly) the simplest product model ever"""

    is_active = models.BooleanField(_('is active'), default=True)
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    ordering = models.PositiveIntegerField(_('ordering'), default=0)

    description = models.TextField(_('description'), blank=True)

    class Meta:
        app_label = 'product'
        ordering = ['ordering', 'name']
        verbose_name = _('product')
        verbose_name_plural = _('products')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('plata_product_detail', (), {'object_id': self.pk})
