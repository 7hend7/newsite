from __future__ import unicode_literals

from django.contrib import messages
from django.db import models
from django.shortcuts import redirect, render

from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField

from taggit.models import Tag, TaggedItemBase

from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel
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
# snippets
from wagtail.snippets.models import register_snippet
# pagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


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

    def get(self, request, *args, **kwargs):
        return super(AppPage, self).get(request, *args, **kwargs)

    # Defines a method to access the children of the page (e.g. BlogPage
    # objects). On the demo site we use this on the HomePage
    def children(self):
        return self.get_children().specific().live()

    def get_livepages(self, request):
        cat_id = request.GET.get('cat_id')
        if cat_id:
            pages = AppPage.objects.live().descendant_of(self).filter(categories__id = cat_id).order_by('-date_published')
        else:
            pages = AppPage.objects.live().descendant_of(self).order_by('-date_published')  # '-first_published_at'
        return pages

    # Pagination for the index page. We use the `django.core.paginator` as any
    # standard Django app would, but the difference here being we have it as a
    # method on the model rather than within a view function
    def paginate(self, request, **kwargs):
        page = request.GET.get('page')
        paginator = Paginator(self.get_livepages(request), 6)
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
        # context['appages'] = appages
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


class AppPage(Page):
    intro = RichTextField(
        help_text='Text to describe the page', blank=True
        )
    '''
    image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='image for Index page'
        )
    '''
    body = StreamField(
        BaseStreamBlock, verbose_name="Page body", blank=True
        )
    subtitle = models.CharField(blank=True, max_length=255)
    tags = ClusterTaggableManager(through=AppPageTag, blank=True)
    date_published = models.DateField(
        "Date article published",
        blank=True,
        null=True
        )

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

    def get_by_category(self):
        res = self.objects.filter(categories=self.categories)
        raise Exception(res.count())
        return res

    content_panels = Page.content_panels + [
        FieldPanel('subtitle', classname="full"),
        FieldPanel('intro', classname="full"),
        # ImageChooserPanel('image'),
        StreamFieldPanel('body'),
        FieldPanel('date_published'),
        FieldPanel('categories'),
        # InlinePanel()
        FieldPanel('tags'),
        InlinePanel('gallery_images', label="Gallery images"),  # gallery_images in AppPageGalleryImages
        ]
    # -
    search_fields = Page.search_fields + [
        index.SearchField('body'),
        ]


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

    context_object_name = "images"
    intro = RichTextField(
    help_text='Text to describe the page', blank=True)

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
    icon = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+')
    # - for model fields "panels"
    panels = [
        FieldPanel('name'),
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
        # -
        context = super().get_context(request)
        context['appages'] = appages
        context['tag'] = tag
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









