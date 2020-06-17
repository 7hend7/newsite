from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.core.fields import StreamField
from newapp.blocks import BaseStreamBlock
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.core.models import Page, Orderable
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from wagtail.admin.edit_handlers import MultiFieldPanel, PageChooserPanel

class HomePage(Page):

    intro = RichTextField(
        help_text='Text to describe the page', blank=True
        )

    # Image foe page
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='Homepage image'
    )

    body = StreamField(
        BaseStreamBlock(), verbose_name="Page body", blank=True
    )

    def get_childs_page(self):
        return self.get_children().specific().live()

    def get_context(self, request):
        context = super().get_context(request)
        context['child_pages'] = self.get_childs_page()
        # raise Exception(str(context))
        return context

    content_panels = Page.content_panels + [
        # FieldPanel('subtitle', classname="full"),
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
        InlinePanel('shown_pages', label="Shown pages"),
        ]


class HomeShownPage(Orderable):
    '''These are the pages which related with homepage here'''
    page = ParentalKey(HomePage, on_delete=models.CASCADE,
                       related_name='shown_pages')
    shown_page = models.ForeignKey('wagtailcore.Page', on_delete=models.CASCADE, related_name='shown_page')
    featured_title = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text='Title to display above the promo copy'
    )
    panels = [
            MultiFieldPanel([
                FieldPanel('featured_title'),
                PageChooserPanel('shown_page'),
            ], heading="Featured homepage sections", classname="collapsible"),        
        ]










