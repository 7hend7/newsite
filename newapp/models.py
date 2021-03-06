from __future__ import unicode_literals
import json
from newsite.settings.base import GOOGLE_MAP_API_KEY
from datetime import datetime
from django.contrib import messages
from django.db import models
from django.shortcuts import redirect, render
from django.core.validators import RegexValidator
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField

from taggit.models import Tag, TaggedItemBase

from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel, FieldRowPanel, MultiFieldPanel

from wagtail.contrib.forms.models import (
    AbstractEmailForm,
    AbstractFormField
)
from wagtail.core.fields import StreamField
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.edit_handlers import SnippetChooserPanel
# blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.core.blocks import (
    CharBlock, ChoiceBlock, RichTextBlock, StreamBlock, StructBlock, TextBlock,
    )

from .blocks import BaseStreamBlock, ImgStreamBlock
# search
from wagtail.search.models import Query
# snippets
from wagtail.snippets.models import register_snippet
# pagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
# wagtailleafletwidget
from wagtailleafletwidget.edit_handlers import GeoPanel
from django.utils.functional import cached_property
from wagtailleafletwidget.helpers import geosgeometry_str_to_struct
# -!-
# from wagtailstreamforms.wagtail_hooks.process_form import hooks


class AppIndexPage(Page):
    intro = RichTextField(
                          help_text='Text to describe the page', blank=True
                          )
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Main image for index page'
        )

    content_panels = Page.content_panels + [
            FieldPanel('intro', classname="full"),
            ImageChooserPanel("image"),
        ]

    subpage_types = ['AppPage']

    # override parent constructor to set slug field
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        self.slug = "app-index-page"

    # Defines a method to access the children of the page (e.g. BlogPage
    # objects). On the demo site we use this on the HomePage
    def children(self):
        return self.get_children().specific().live()

    # -
    def get_livepages(self, request):
        self.cat_id = request.GET.get('cat_id')
        self.tag = request.GET.get('tag')
        self.date_p = request.GET.get("date-nav")
        self.cat = None
        pages = None
        # -
        if self.date_p:
            # raise Exception(self.date_p)
            self.date_p = datetime.strptime(self.date_p, '%d/%m/%Y')
            self.date_p = self.date_p.strftime('%Y-%m-%d')
            pages = AppPage.objects.live().descendant_of(self).filter(date_published=self.date_p)            
        # -
        if self.cat_id:
            pages = AppPage.objects.live().descendant_of(self).filter(categories__id=self.cat_id).order_by('-date_published')
            self.cat = AppCategory.objects.filter(id=self.cat_id).first()
            # raise Exception(self.cat)
        if self.tag:
            pages = AppPage.objects.live().descendant_of(self).filter(tags__name=self.tag).order_by('-date_published')
        if not pages:
            pages = AppPage.objects.live().descendant_of(self).order_by('-date_published')  # '-first_published_at'
        return pages

    # Pagination for the index page. We use the `django.core.paginator` as any
    # standard Django app would, but the difference here being we have it as a
    # method on the model rather than within a view function
    def paginate(self, request, **kwargs):
        page = request.GET.get('page')
        paginator = Paginator(self.get_livepages(request), 12)
        try:
            pages = paginator.page(page)
        except PageNotAnInteger:
            pages = paginator.page(1)
        except EmptyPage:
            pages = paginator.page(paginator.num_pages)
        return pages

    def get_context(self, request):
        context = super().get_context(request)
        # get AppPage objects
        # appages = self.get_children().live().order_by("-first_published_at")
        # AppPage.objects.descendant_of(self).live().order_by('-date_published')
        context['appages'] = self.paginate(request)
        context['category'] = self.cat
        context['tag'] = self.tag
        return context

    def __str__(self):
        return "<<{}>>".format(self.title)


class AppPageTag(TaggedItemBase):
    """
    This model allows us to create a many-to-many relationship between
    the AppPage object and tags. There's a longer guide on using it at
    http://docs.wagtail.io/en/latest/reference/pages/model_recipes.html#tagging
    """
    content_object = ParentalKey('AppPage',
                                related_name='tagged_items', on_delete=models.CASCADE)


class ImgPageTag(TaggedItemBase):
    content_object = ParentalKey('ImgPage',
                                 related_name='tagged_items', on_delete=models.CASCADE)


class AppPage(Page):  # RoutablePageMixin
    intro = RichTextField(
        help_text='Text to describe the page', blank=True
        )

    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Banner image for page'
        )

    body = StreamField(
        BaseStreamBlock, verbose_name="Page body", blank=True
        )
    subtitle = models.CharField(blank=True, max_length=255)
    tags = ClusterTaggableManager(through=AppPageTag, blank=True)
    date_published = models.DateField(
        "Date article published",
        blank=False,
        null=False
        )

    # geo location coord field
    latlng = models.CharField(max_length=128,
                              default=None,
                              null=True,
                              blank=True,
                              help_text="Comma separated lat/long. (Ex. 64.144367, -21.939182) \
                              Right click Google Maps and select 'What\'s Here'",
                              #validators=[
                              #    RegexValidator(
                              #        regex=r'^(\-?\d+(\.\d+)?),\s*(\-?\d+(\.\d+)?)$',
                              #        message='Lat Long must be a comma-separated numeric lat and long',
                              #        code='invalid_lat_long'
                              #        ),
                              #    ] 
                              )
    @cached_property
    def point(self):
        return geosgeometry_str_to_struct(self.latlng)

    @property
    def lat(self):
        return self.point['y']

    @property
    def lng(self):
        return self.point['x']

    # -
    likes = models.PositiveIntegerField(null=True, blank=True, default=0)
    categories = ParentalManyToManyField('newapp.AppCategory', blank=True)

    def get_first_image(self):
        # return None
        # return AppPageGalleryImage.objects.first(). # .first()
        apg = AppPageGalleryImage.objects.filter(page__id=self.id).first()
        img = apg.image  # .file
        return img

    def get_image_count(self):
        return AppPageGalleryImage.objects.filter(page__id=self.id).count()

    def get_page_images(self):
        return AppPageGalleryImage.objects.filter(page__id=self.id)

    def get_next_page(self):
        res = self.get_next_by_date_published()
        # raise Exception(res)
        return res

    def get_prev_page(self):
        # raise Exception(self)
        res = self.get_previous_by_date_published()
        # raise Exception(res)
        return res

    def get_tag_items_bycount(count=5):
        tags = AppPage.tags.all()
        res = [tags[i:i + count] for i in range(0, len(tags), count)]
        return res

    def get_page_bypopular():
        res = []
        res = AppPage.objects.live().order_by("-likes")[:5]
        return res

    # Additional method to serving request!
    # We serve AJAX request
    def serve(self, request, *args, **kwargs):
        page_id = str(self.id)

        if request.is_ajax():
            self.session = request.session
            self.session.set_expiry(None)
            # self.session.flush()
            # raise Exception(self.session["addLike"])
            self.addlike = self.session.get("addlike")
            if not self.addlike:
                self.addlike = self.session["addlike"] = {}
            if page_id not in self.addlike:
                self.addlike[page_id] = "1"
                request.session.modified = True
                self.likes += 1
                self.save()
            res = {"likes_count": str(self.likes)}
            json_output = json.dumps(res)
            return HttpResponse(json_output)
        else:
            return super().serve(request, *args, **kwargs)

    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('image'),
        StreamFieldPanel('body'),
        FieldPanel('date_published'),
        FieldPanel('categories'),
        # InlinePanel()
        FieldPanel('tags'),
        InlinePanel('gallery_images', label="Gallery images"),  # gallery_images in AppPageGalleryImages
        # geo location
        GeoPanel('latlng'),
        ]
    # -
    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.FilterField('date_published'),
        index.SearchField('intro'),
        index.SearchField('title'),
        index.SearchField('subtitle'),
        ]

    def get_context(self, request):
        context = super().get_context(request)
        if self.latlng:
            context['lat'] = self.lat
            context['long'] = self.lng
            context['google_map_api_key'] = GOOGLE_MAP_API_KEY
        return context

class ImgPage(Page):
    '''Galery images page'''
    image = models.ForeignKey(
       'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Main image for gallery page'
        )

    # context_object_name = "gallery"
    intro = RichTextField(
        help_text='Text to describe the page', blank=True)
    # It is for images colection field
    images = StreamField(
        ImgStreamBlock, verbose_name="Images", blank=True)

    date_published = models.DateField(
        "Date page published",
        blank=True,
        null=True
        )
    tags = ClusterTaggableManager(through=ImgPageTag, blank=True)
    categories = ParentalManyToManyField('newapp.AppCategory', blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        StreamFieldPanel('images'),
        FieldPanel('date_published'),
        FieldPanel('categories'),
        FieldPanel('tags'),
        ImageChooserPanel("image"),
        ]

    def get_context(self, request):
        context = super().get_context(request)
        return context


class AppPageGalleryImage(Orderable):
    '''Images witch related with AppPage'''
    page = ParentalKey(AppPage, on_delete=models.CASCADE,
                       related_name='gallery_images')
    image = models.ForeignKey('wagtailimages.Image', on_delete=models.CASCADE, related_name='image')
    caption = models.CharField(blank="True", max_length=250)
    panels = [ImageChooserPanel('image'), FieldPanel('caption')]


@register_snippet
class AppCategory(models.Model):
    name = models.CharField(max_length=255)
    intro = RichTextField(
        help_text='Text to describe the category', blank=True) 
    icon = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+')
    # - for model fields "panels"
    panels = [
        FieldPanel('name'),
        FieldPanel('intro'),
        ImageChooserPanel('icon')
        ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class AppTagIndexPage(Page):

    def get_context(self, request):
        # filter by tag
        tag = request.GET.get('tag')
        appages = AppPage.objects.filter(tags__name=tag)
        # raise Exception(tag)
        # -
        context = super().get_context(request)
        context['appages'] = appages
        # context['tag'] = tag
        return context


@register_snippet
class FooterText(models.Model):
    """
    This provides editable text for the site footer. Again it uses the decorator
    `register_snippet` to allow it to be accessible via the admin. It is made
    accessible on the template via a template tag defined in base/templatetags/
    navigation_tags.py
    """
    body = RichTextField()

    panels = [
        FieldPanel('body'),
    ]

    def __str__(self):
        return "Footer text"

    class Meta:
        verbose_name_plural = 'Footer Text'


@register_snippet
class DefaultBannerImage(models.Model):
    """ """
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Default image for banner/logo'
        )

    panels = [
        ImageChooserPanel("image"),
        ]

    def __str__(self):
        return "Default banner/logo image"

    class Meta:
        verbose_name_plural = 'Default image for banner/logo'


class FormField(AbstractFormField):
    page = ParentalKey(
        'ContactPage',
        on_delete=models.CASCADE,
        related_name='form_fields',
    )


class ContactPage(AbstractEmailForm):

    # template = "contact_page.html"
    # This is the default path.
    # If ignored, Wagtail adds _landing.html to your template name
    # landing_page_template = "contact_page_landing.html"

    intro = RichTextField(blank=True)
    thank_you_text = RichTextField(blank=True)

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel('intro'),
        InlinePanel('form_fields', label='Form Fields'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel("subject"),
        ], heading="Email Settings"),
    ]


