### Modules ###
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pandas as pd
import csv
import requests
import re
import datetime
from unidecode import unidecode

### Classes ###
class Fact:
    def __init__(self, num, genre, link, price, date):
        self._link = link
        self._num = num
        self._genre = genre
        self._price = price
        self._date = date

    def print(self):
        print('URL: ', self._link)
        print('POZYCJA: ', self._num)
        print('GATUNEK: ', unidecode(self._genre))
        print('CENA: ', self._price)
        print('DATA: ', self._date)
        print('\n')

    def tolist(self):
        return [self._link, self._num, self._genre, self._price, self._date]

class Book:
    def __init__(self, link, title, author, price, cover, publisher, page_count, site, img_url):
        self._link = link
        self._title = title
        self._author = author
        self._price = price
        self._cover = cover
        self._publisher = publisher
        self._page_count = page_count
        self._site = site
        self._img_url = img_url

    def print(self):
        print("URL: ", self._link)
        print("TYTUL: ", unidecode(self._title))
        print("AUTOR: ", unidecode(self._author))
        print("ORYGINALNA CENA: ", self._price)
        print("OKLADKA: ", unidecode(self._cover))
        print("WYDAWCA: ", unidecode(self._publisher))
        print("LICZBA STRON: ", self._page_count)
        print("KSIEGARNIA: ", unidecode(self._site))
        print("LINK DO OKLADKI: ", self._img_url)
        print("\n")

    def tolist(self):
        return [self._link, self._title, self._author, self._price, self._cover, self._publisher, self._page_count, self._site, self._img_url]

    def tolist_unidecode(self):
        return [self._link, unidecode(self._title), self._author, self._price, self._cover, self._publisher, self._page_count, self._site, self._img_url]

### Functions ###
def getPage(url, headers):
    try:
        req = requests.get(url, headers=headers)
    except requests.exceptions.RequestException:
        print("An error occured!")
        return None
    return BeautifulSoup(req.text, 'html.parser')

def getAbsoluteURL(baseUrl, source):
    if source.startswith('https://www.'):
        url = 'https://{}'.format(source[12:])
    elif source.startswith('https://'):
        url = source
    elif source.startswith('www.'):
        url = source[4:]
        url = 'https://{}'.format(source)
    elif source.startswith('/'):
        url = '{}{}'.format(baseUrl, source)
    else:
        url = '{}/{}'.format(baseUrl, source)
    if baseUrl not in url:
        return None
    return url

def getPrice(priceTag):
    return float(priceTag[1:int(len(priceTag)/2)-3].replace(',', '.'))

def empikFactsCsv(titles, cat, file):
    baseurl = "https://www.empik.com"
    for title in titles:
        bookPosition = int(title.find('strong', {'class':'ta-product-title'}).find('span', {'class':'blue-number'}).get_text())
        bookGenre = cat
        bookURL = getAbsoluteURL(baseurl, title.find('a')['href'])
        try:
            bookPrice = title.find('div', {'class':'price ta-price-tile'}).get_text(strip=True)
            temp = bookPrice.find("zł")
            bookPrice = bookPrice[:temp-1:]
        except AttributeError:
            bookPrice = "-"
        bookTimestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        book = Fact(bookPosition, bookGenre, bookURL, bookPrice, bookTimestamp)
        book.print()
        file.writerow(book.tolist())

def scrapEmpik(cat_csv, headers, file):
    for site, cat in zip(cat_csv['Empik'], cat_csv['Kategoria']):
        bs = getPage(site, headers)
        titles = bs.find('div', {'class':'search-content js-search-content'}).find_all('div', {'class':'search-list-item js-reco-product js-energyclass-product ta-product-tile'})
        empikFactsCsv(titles, cat, file)
        next_page = bs.find('div', {'class':'pagination'}).find('a', href=re.compile('^(\?searchCategory)'))['href']
        new_url = urlparse(site)
        new_url = "{}://{}{}{}".format(new_url.scheme, new_url.netloc, new_url.path, next_page)
        bs = getPage(new_url, headers)
        titles = bs.find('div', {'class':'search-content js-search-content'}).find_all('div', {'class':'search-list-item js-reco-product js-energyclass-product ta-product-tile'})
        empikFactsCsv(titles, cat, file)

def skFactsCsv(titles, cat, file):
    baseurl = "https://www.swiatksiazki.pl"
    for title in titles:
        bookPosition = int(title.find('span', {'class':'bestseller-position'}).get_text())
        bookGenre = cat
        bookURL = title.find('a', {'class':'product photo product-item-photo'})['href']
        bookPrice = title.find('span', {'class':'price'}).get_text(strip=True)
        bookPrice = bookPrice[:len(bookPrice)-3:]
        bookTimestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        book = Fact(bookPosition, bookGenre, bookURL, bookPrice, bookTimestamp)
        book.print()
        file.writerow(book.tolist())

def scrapSk(cat_csv, headers, file):
    for site, cat in zip(cat_csv['Swiatksiazki'], cat_csv['Kategoria']):
        bs = getPage(site, headers)
        titles = bs.find_all('div', {'class':'product-item-info'})
        skFactsCsv(titles, cat, file)
        products_flag = int(bs.find('p', {'class':'toolbar-amount'}).find('span').get_text(strip=True))
        if products_flag <= 50:
            continue
        next_page = bs.find('div', {'class':'pages'}).find('a', {'class':'action next'})['href']
        bs = getPage(next_page, headers)
        titles = bs.find_all('div', {'class':'product-item-info'})
        skFactsCsv(titles, cat, file)

def scrapBook(books, added, headers, file):
    for book in books:
        if book in added['URL'].unique():
            continue
        site = urlparse(book).netloc
        bs = getPage(book, headers)
        if site == 'www.empik.com':
            bookTitle = bs.find('h1', {'itemprop':'name'}).get_text(strip=True).replace(u'\xa0', u' ')
            if bookTitle.find('(wydanie pocket)') != -1:
                bookTitle = bookTitle[:bookTitle.find('(wydanie pocket)'):]
            if bookTitle.find('(okładka') != -1:
                bookTitle = bookTitle[:bookTitle.find('(okładka'):]
            bookCover = bs.find('span', {'class':'ta-product-carrier'}).get_text(strip=True).replace(u'\xa0', u' ')
            if not bookCover:
                bookCover = '-'
            else:
                bookCover = bookCover.replace('okładka ', '')
                bookCover = bookCover.replace('(', '')
                bookCover = bookCover.replace(')', '')
            try:
                bookAuthor = bs.find('span', {'class':'pDAuthorList'}).get_text(strip=True).replace(u'\xa0', u' ')
            except AttributeError:
                bookAuthor = "Brak autora"
            try:
                bookPrice = bs.find('span', {'class':'ta-oldprice'}).get_text(strip=True)
                if not bookPrice:
                    bookPrice = bs.find('span', {'class':'ta-price'}).get_text(strip=True)
                bookPrice = bookPrice[:bookPrice.find('zł')-1:]
            except AttributeError:
                bookPrice = "-"
            bookPublisher = bs.find('table', {'class':'productBaseInfo__info'}).find('a').get_text(strip=True)
            list = bs.find('table', {'class':'productBaseInfo__info'}).find_all('tr')
            bookPageCount = '-'
            for el in list:
                el = el.get_text(strip=True)
                temp = el.find("Liczba stron:")
                if temp != -1:
                    bookPageCount = el[temp+13::]
                    break
            bookImgUrl = bs.find('img', {'itemprop':'image'})['src']
            new = Book(book, bookTitle, bookAuthor, bookPrice, bookCover, bookPublisher, bookPageCount, 'Empik', bookImgUrl)
            try:
                file.writerow(new.tolist())
            except UnicodeEncodeError:
                file.writerow(new.tolist_unidecode())
            new.print()
        elif site == 'www.swiatksiazki.pl':
            bookTitle = bs.find('h1', {'class':'page-title'}).get_text(strip=True)
            if bookTitle == 'Przepraszamy, wystąpił błąd':
                continue
            try:
                bookAuthor = bs.find('li', {'class':'prod-author'}).get_text(strip=True)
                bookAuthor = bookAuthor[bookAuthor.find(':')+1::]
                if not bookAuthor:
                    bookAuthor = 'Brak autora'
            except AttributeError:
                bookAuthor = "Brak autora"       
            bookPrice = bs.find('span', {'class':'old-price'}).get_text(strip=True)
            bookPrice = bookPrice[:bookPrice.find(' ')-2:]
            try:
                bookPublisher = bs.find('a', href=re.compile('^(/wydawca/)')).get_text(strip=True)
            except AttributeError:
                bookPublisher = "-"
            bookImgUrl = bs.find('div',{'class':'gallery-image-wrapper'}).find('img')['src']
            list = bs.find('ul', {'class':'product-info-attributes'}).find_all('li')
            bookPageCount = '-'
            bookCover = '-'
            for el in list:
                el = el.get_text(strip=True)
                temp1 = el.find('Ilość stron:')
                temp2 = el.find('Typ okładki:')
                if temp1 != -1:
                    bookPageCount = el[12::]
                if temp2 != -1:
                    bookCover = el[12::]
                    bookCover = bookCover.replace(' okładka', '')
            new = Book(book, bookTitle, bookAuthor, bookPrice, bookCover, bookPublisher, bookPageCount, 'SwiatKsiazki', bookImgUrl)
            try:
                file.writerow(new.tolist())
            except UnicodeEncodeError:
                file.writerow(new.tolist_unidecode())
            new.print()


### MAIN ###
session = requests.Session()
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
           'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'Accept-Language':'pl'}

categories = pd.read_csv(r'books_categories.csv', delimiter = ';', encoding = 'utf8')
print("----- Zbieranie informacji o aktualnych bestsellerach -----\n\n")
with open('facts.csv', 'a+', encoding='cp1250', newline='') as f_object:
    writer_object = csv.writer(f_object, delimiter = ';')
    scrapEmpik(categories, headers, writer_object)
    scrapSk(categories, headers, writer_object)
    f_object.close()

books = pd.read_csv(r'facts.csv', delimiter = ';', encoding = 'cp1250')
added = pd.read_csv(r'books.csv', delimiter = ';', encoding = 'cp1250')
print("\n\n----- Zbieranie informacji o nowych ksiazkach -----\n\n")
with open('books.csv', 'a+', encoding='cp1250', newline='') as f_object:
    writer_object = csv.writer(f_object, delimiter = ';')
    books = books['URL'].unique()
    scrapBook(books, added, headers, writer_object)
    f_object.close()
 