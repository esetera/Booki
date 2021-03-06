import os

from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse,HttpResponseRedirect
from django.contrib.auth.models import User

from booki.editor import models
from booki.utils import pages
from booki.editor.views import getVersion
from django.conf import settings

# this is just temporary
def _customCSSExists(bookName):
    """
    Check if this book has custom CSS file.

    @type bookName: C{string}
    @param bookName: Unique Book ID
    @rtype: C{boolean}
    @return: Return False or True
    """
    return os.path.exists('%s/css/book.%s.css' % (settings.STATIC_ROOT, bookName))

def view_full(request, bookid, version=None):
    """
    Django View. Shows full content of book on one page. This is published version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Django Request
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param version: Version of the book
    """

    chapters = []

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = getVersion(book, version)

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            chapters.append({"type": "chapter",
                             "title": chapter.chapter.title,
                             "content": chapter.chapter.content,
                             "chapter": chapter.chapter})
        else:
            chapters.append({"type": "section",
                             "title": chapter.name})

    return render_to_response('reader/full.html', {"book": book, 
                                                   "book_version": book_version.getVersion(),
                                                   "chapters": chapters, 
                                                   "has_css": _customCSSExists(book.url_title),
                                                   "request": request})


def book_info(request, bookid, version=None):
    """
    Django View. Shows single page with all the Book info.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})


    book_version = getVersion(book, version)

    book_history =  models.BookHistory.objects.filter(version = book_version).order_by("-modified")[:20]

    book_collaborators =  [e.values()[0] for e in models.BookHistory.objects.filter(version = book_version, kind = 2).values("user__username").distinct()]
    
    import sputnik
    channel_name = "/booki/book/%s/%s/" % (book.id, book_version.getVersion())
    online_users = sputnik.smembers("sputnik:channel:%s:users" % channel_name)

    book_versions = models.BookVersion.objects.filter(book=book).order_by("created")

    return render_to_response('reader/book_info.html', {"book": book, 
                                                        "book_version": book_version.getVersion(),
                                                        "book_versions": book_versions,
                                                        "book_history": book_history, 
                                                        "book_collaborators": book_collaborators,
                                                        "has_css": _customCSSExists(book.url_title),
                                                        "online_users": online_users,
                                                        "request": request})

def draft_book(request, bookid, version=None):
    """
    Django View. Shows main page for the draft version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})


    book_version = getVersion(book, version)

    chapters = []

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            chapters.append({"url_title": chapter.chapter.url_title,
                             "name": chapter.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chapter.name})
        

    return render_to_response('reader/draft_book.html', {"book": book, 
                                                   "book_version": book_version.getVersion(),
                                                   "chapters": chapters, 
                                                   "has_css": _customCSSExists(book.url_title),
                                                   "request": request})

def draft_chapter(request, bookid, chapter, version=None):
    """
    Django View. Shows chapter for the draft version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type chapter: C{string}
    @param chapter: Chapter name
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = getVersion(book, version)

    chapters = []

    for chap in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chap.isChapter():
            chapters.append({"url_title": chap.chapter.url_title,
                             "name": chap.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chap.name})

    try:
        content = models.Chapter.objects.get(version=book_version, url_title = chapter)
    except models.Chapter.DoesNotExist:
        return pages.ErrorPage(request, "errors/chapter_does_not_exist.html", {"chapter_name": chapter, "book": book})
    except models.Chapter.MultipleObjectsReturned:
        return pages.ErrorPage(request, "errors/chapter_duplicate.html", {"chapter_name": chapter, "book": book})
        
    return render_to_response('reader/draft_chapter.html', {"chapter": chapter, 
                                                      "book": book, 
                                                      "book_version": book_version.getVersion(),
                                                      "chapters": chapters, 
                                                      "has_css": _customCSSExists(book.url_title),
                                                      "request": request, 
                                                      "content": content})



def book_view(request, bookid, version=None):
    """
    Django View. Shows main book page for the published version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})


    book_version = getVersion(book, version)

    chapters = []

    for chapter in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chapter.isChapter():
            chapters.append({"url_title": chapter.chapter.url_title,
                             "name": chapter.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chapter.name})
        

    return render_to_response('reader/book_view.html', {"book": book, 
                                                   "book_version": book_version.getVersion(),
                                                   "chapters": chapters, 
                                                   "has_css": _customCSSExists(book.url_title),
                                                   "request": request})



def book_chapter(request, bookid, chapter, version=None):
    """
    Django View. Shows chapter for the published version of a book.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type chapter: C{string}
    @param chapter: Chapter name
    @type version: C{string}
    @param verson: Book version
    """

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = getVersion(book, version)

    chapters = []

    for chap in  models.BookToc.objects.filter(version=book_version).order_by("-weight"):
        if chap.isChapter():
            chapters.append({"url_title": chap.chapter.url_title,
                             "name": chap.chapter.title})
        else:
            chapters.append({"url_title": None,
                             "name": chap.name})

    try:
        content = models.Chapter.objects.get(version=book_version, url_title = chapter)
    except models.Chapter.DoesNotExist:
        return pages.ErrorPage(request, "errors/chapter_does_not_exist.html", {"chapter_name": chapter, "book": book})
    except models.Chapter.MultipleObjectsReturned:
        return pages.ErrorPage(request, "errors/chapter_duplicate.html", {"chapter_name": chapter, "book": book})


    return render_to_response('reader/book_chapter.html', {"chapter": chapter, 
                                                      "book": book, 
                                                      "book_version": book_version.getVersion(),
                                                      "chapters": chapters, 
                                                      "has_css": _customCSSExists(book.url_title),
                                                      "request": request, 
                                                      "content": content})

# PROJECT

def attachment(request, bookid,  attachment, version=None):
    """
    Django View. Returns content of an attachment.

    @todo: Not sure if this is even used anymore

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type attachment: C{string}
    @param attachment: Name of the attachment
    @type version: C{string}
    @param version: Version of the book
    """

    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})
        
    book_version = getVersion(book, version)

    path = '%s/%s' % (version, attachment)

    document_root = '%s/books/%s/' % (settings.DATA_ROOT, bookid)

    return static.serve(request, path, document_root)


def staticattachment(request, bookid,  attachment, version=None, chapter = None):
    """
    Django View. Returns content of an attachment.

    @todo: It is wrong in so many different levels to serve attachments this way.

    @type request: C{django.http.HttpRequest}
    @param request: Client Request object
    @type bookid: C{string}
    @param bookid: Unique Book ID
    @type attachment: C{string}
    @param attachment: Name of the attachment
    @type version: C{string}
    @param version: Version of the book
    """

    from django.views import static

    try:
        book = models.Book.objects.get(url_title__iexact=bookid)
    except models.Book.DoesNotExist:
        return pages.ErrorPage(request, "errors/book_does_not_exist.html", {"book_name": bookid})

    book_version = getVersion(book, version)

    path = '%s/%s' % (book_version.getVersion(), attachment)

    document_root = '%s/books/%s/' % (settings.DATA_ROOT, bookid)

    return static.serve(request, path, document_root)

