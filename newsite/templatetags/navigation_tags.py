from django import template
import re
from django.template.defaultfilters import stringfilter
from wagtail.core.models import Page, Site

from newapp.models import FooterText, AppPageTag, AppCategory, AppPage


register = template.Library()
# https://docs.djangoproject.com/en/1.9/howto/custom-template-tags/


@register.simple_tag(takes_context=True)
def get_site_root(context):
    # This returns a core.Page. The main menu needs to have the site.root_page
    # defined else will return an object attribute error ('str' object has no
    # attribute 'get_children')
    return Site.find_for_request(context['request']).root_page


def has_menu_children(page):
    # This is used by the top_menu property
    # get_children is a Treebeard API thing
    # https://tabo.pe/projects/django-treebeard/docs/4.0.1/api.html
    return page.get_children().live().in_menu().exists()


def has_children(page):
    # Generically allow index pages to list their children
    return page.get_children().live().exists()


def is_active(page, current_page):
    # To give us active state on main navigation
    return (current_page.url_path.startswith(page.url_path) if current_page else False)


# Retrieves the top menu items - the immediate children of the parent page
# The has_menu_children method is necessary because the Foundation menu requires
# a dropdown class to be applied to a parent
@register.inclusion_tag('tags/top_menu.html', takes_context=True)
def top_menu(context, parent, calling_page=None):
    menuitems = parent.get_children().live().in_menu()
    for menuitem in menuitems:
        menuitem.show_dropdown = has_menu_children(menuitem)
        # We don't directly check if calling_page is None since the template
        # engine can pass an empty string to calling_page
        # if the variable passed as calling_page does not exist.
        menuitem.active = (calling_page.url_path.startswith(menuitem.url_path)
                           if calling_page else False)
    return {
        'calling_page': calling_page,
        'menuitems': menuitems,
        # required by the pageurl tag that we want to use within this template
        'request': context['request'],
    }


# Retrieves the children of the top menu items for the drop downs
@register.inclusion_tag('tags/top_menu_children.html', takes_context=True)
def top_menu_children(context, parent, calling_page=None):
    menuitems_children = parent.get_children()
    menuitems_children = menuitems_children.live().in_menu()
    for menuitem in menuitems_children:
        menuitem.has_dropdown = has_menu_children(menuitem)
        # We don't directly check if calling_page is None since the template
        # engine can pass an empty string to calling_page
        # if the variable passed as calling_page does not exist.
        menuitem.active = (calling_page.url_path.startswith(menuitem.url_path)
                           if calling_page else False)
        menuitem.children = menuitem.get_children().live().in_menu()
    return {
        'parent': parent,
        'menuitems_children': menuitems_children,
        # required by the pageurl tag that we want to use within this template
        'request': context['request'],
    }


@register.inclusion_tag('tags/breadcrumbs.html', takes_context=True)
def breadcrumbs(context):
    self = context.get('self')
    # if self is None or self.depth <= 2:
        # When on the home page, displaying breadcrumbs is irrelevant.
    #    ancestors = ()
    # else:
        # get parents pages
    ancestors = Page.objects.ancestor_of(
            self, inclusive=True).filter(depth__gt=1)
    return {
        'ancestors': ancestors,
        'request': context['request'],
    }


@register.inclusion_tag('includes/footer_text.html', takes_context=True)
def get_footer_text(context):
    footer_text = ""
    if FooterText.objects.first() is not None:
        footer_text = FooterText.objects.first().body

    return {
        'footer_text': footer_text,
    }


@register.inclusion_tag('tags/tagged_items.html', takes_context=True)
def get_tagged_items(context):
    tag_pages = AppPage.get_tag_items_bycount()# AppPage.tags.all()
    #for tag in tag_pages:
    #    raise Exception(tag)
    return{
        'tag_pages': tag_pages,
        'request': context['request'],
    }


@register.inclusion_tag('tags/category_list.html', takes_context=True)
def get_category_list(context):
    cat_list = AppCategory.objects.all()
    return{
        'cat_list': cat_list,
        'request': context['request'],
    }

@register.inclusion_tag('tags/popular_list.html', takes_context=True)
def get_popular_list(context):
    pop_list = AppPage.get_page_bypopular()
    return{
        'popular_list': pop_list,
        'request': context['request'],
    }

# Our filter for parse and changing youtube URL "https://www.danielms.site/blog/wagtail-embedurl-youtube-tags/"
@register.filter(name="embedurl")
def get_embed_url(url):
    if "youtube.com" in url or "youtu.be" in url:
        regex = r"(?:https:\/\/)?(?:www\.)?(?:youtube\.com|youtu\.be)\/(?:watch\?v=)?(.+)"  # Get video id from URL
        embed_url = re.sub(
            regex, r"https://www.youtube.com/embed/\1", url
        )  # Append video id to desired URL
        # print(embed_url)
        embed_url_with_parameters = embed_url + "?rel=0"  # Add additional parameters
        return embed_url_with_parameters
    else:
        return None













