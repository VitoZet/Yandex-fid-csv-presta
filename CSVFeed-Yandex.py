from settings import api_key, api_url
from prestashop_api import PrestashopApi
from bs4 import BeautifulSoup
from datetime import datetime
import csv




api = PrestashopApi(api_url, api_key)

def get_product_ids(id_category):
    '''
    Получаем список id товаров из выбраной категории
    '''
    try:
        product_api = api.get('categories/'+str(id_category))
        list_id_products_category = [id_product['id'] for id_product in
                                     product_api['category']['associations']['products']['product']]
        return list_id_products_category
    except:
        print('Нет доступа по API, похоже сайт лёг')


def sorting_activity_id(list_id_products_category):
    '''
    Сортирует по активности ID товаров
    Не активные сохраняются в файл тхт в корень
    Удаленные ID сохраняются в файл тхт в корень
    Возращает list активных ID
    '''

    list_product_active = []
    list_product_not_active = []
    list_id_product_error = []

    for e,id_product in enumerate(list_id_products_category):
        print('Сортирую по активности. Осталось: ' + str(len(list_id_products_category) - e))
        try:
            product_api = api.get('products/' + str(id_product))
            product_active = product_api['product']['active']
            if product_active == '1':
                list_product_active.append(id_product)
            else:
                list_product_not_active.append(id_product)
        except:
            print('Нет доступа по API, похоже сайт лёг')

    print('Всего активных ID: ' + str(len(list_product_active)) + ' шт.')
    print('_____________')
    print('Не активных ID: ' + str(len(list_product_not_active)) + ' шт.')
    print(list_product_not_active)
    print('_____________')
    print('Удаленные ID: ' + str(len(list_id_product_error)) + ' шт.')
    print(list_id_product_error)

    file_no_active_id = open('NoActiveID-'+str(datetime.now().strftime("%Y%m%d-%H%M%S"))+'.txt', 'w')
    file_no_active_id.write("\n".join(list_product_not_active))
    file_no_active_id.close()

    fileErrorID = open('ErrorID-'+str(datetime.now().strftime("%Y%m%d-%H%M%S"))+'.txt', 'w')
    fileErrorID.writelines("\n".join(list_id_product_error))
    fileErrorID.close()

    print('Товары по активности рассортированы')
    return list_product_active



def get_product_ids_in_stock(sorting_activity_id):
    '''
    Возращает  список ID товаров в наличии
    Сохраняет файл тхт ID товаров не в наличии
    '''

    list_on_stock = []
    list_not_stock = []

    for e,id_stock in enumerate(sorting_activity_id):
        print('Сортирую по наличию. Осталось: ' + str(len(sorting_activity_id) - e))
        try:
            id_stock_api = api.get('products/' + str(id_stock))
            if int(id_stock_api['product']['quantity']['#text']) > 0:
                list_on_stock.append(id_stock)
            else:
                list_not_stock.append(id_stock)
        except:
            print('Нет доступа по API, похоже сайт лёг')

    print('Всего ID в наличии: ' + str(len(list_on_stock)) + ' шт.')
    # print(list_on_stock)
    print('_____________')
    print('Всего ID не в наличии: ' + str(len(list_not_stock)) + ' шт.')
    # print(list_not_stock)

    fileNoStock = open('NoStockID-' + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + '.txt', 'w')
    fileNoStock.write("\n".join(list_not_stock))
    fileNoStock.close()

    return list_on_stock


def product_ids_combinations(id_product):
    '''
    Проверка на наличие комбиннаций, возвращает список id комбинаций
    Если кобинаций товара нет, возращает пустой список.
    '''
    list_id_combination_product = []
    id_combinatiop_product_api = api.get('products/' + str(id_product))

    if len(id_combinatiop_product_api['product']['associations']['combinations']) == 2:
        print(str(id_product) + ' - нету кобинаций')

    else:

        if type(id_combinatiop_product_api['product']['associations']['combinations']['combination']) == list:
            for id_combination in id_combinatiop_product_api['product']['associations']['combinations']['combination']:
                list_id_combination_product.append(id_combination['id'])

        else:
            list_id_combination_product.append(
                id_combinatiop_product_api['product']['associations']['combinations']['combination']['id'])

    return list_id_combination_product


def min_price_combinations_product_and_reference(product_ids_combinations, price_product_default):
    '''
    Возвращает минимальную стоимость комбинации которая есть в наличии
    Если комбинаций нет возращает цену по уолчанию
    Возвращает список артикулов для добавления в дискрипшн
    '''
    list_price_combinations = []
    list_reference = []
    for id_combination in product_ids_combinations:
        combinations_api = api.get('combinations/' + str(id_combination))
        list_price_combinations.append(float(combinations_api['combination']['price']) + price_product_default)
        list_reference.append(combinations_api['combination']['reference'])

    return min(list_price_combinations), list_reference

def removes_html_tags(description_html):
    '''
    Очистка описания от тегов HTML
    '''
    soup = BeautifulSoup(description_html, "lxml")
    return soup.get_text().strip()

def parsing_product(list_on_stock, id_category):
    '''
    Парсим продукт
    '''
    data = []
    available = 'true'
    currencyId = 'RUR'
    delivery = 'true'
    pickup = 'true'

    for e, id_product in enumerate(list_on_stock):

        print('Парсинг - ID: ' + str(id_product) + ' Осталось: ' + str(len(list_on_stock) - e))

        try:
            product_api = api.get('products/' + str(id_product))
            category_api = api.get('categories/' + str(id_category))
            category = category_api['category']['name']['language']['#text']
        except:
            print('Нет доступа по API, похоже сайт лёг')

        id = product_api['product']['id']
        friendly_URL = str(product_api['product']['link_rewrite']['language']['#text'])
        url = 'https://fisherpoint.ru/' + friendly_URL + '.html'
        picture = 'https://fisherpoint.ru/' + str(product_api['product']['id_default_image']['#text']) + '-thickbox_default/' + friendly_URL + '.jpg'

        try:
            vendor = product_api['product']['manufacturer_name']['#text']
        except:
            vendor = ''

        name = product_api['product']['name']['language']['#text']

        price_product_default = float(product_api['product']['price'])


        try:
            list_reference = min_price_combinations_product_and_reference(product_ids_combinations(id_product), price_product_default)[1]
        except:
            list_reference = [product_api['product']['reference']]


        try:
            description = removes_html_tags(product_api['product']['description']['language']['#text']) + ' Артикулы: ' + ', '.join(list_reference)
        except:
            description = 'Описание в процесе наплнения' + 'Артикулы: ' + ', '.join(list_reference)

        if product_ids_combinations(id_product):
            price = min_price_combinations_product_and_reference(product_ids_combinations(id_product), price_product_default)[0]

        else:
            price = price_product_default

        data.append([id, available, delivery, pickup, url, vendor, name, category, price, currencyId, picture, description])

    return data


def csv_writer(data_products):
    with open('fid-' + str(datetime.now().strftime("%Y%m%d-%H%M%S")) + '.csv', "w", newline='', encoding='utf-8') as out_file:

        fieldnames = ['id', 'available', 'delivery', 'pickup', 'url', 'vendor', 'name', 'category', 'price', 'currencyId', 'picture', 'description']
        writer = csv.writer(out_file, delimiter=';')
        writer.writerow(fieldnames)
        writer.writerows(data_products)


if __name__ == '__main__':
    id_category = input('Введите ID категории, для которой требуеться создать Тоаварный Фид Яндекса: ')
    csv_writer(parsing_product(get_product_ids_in_stock(sorting_activity_id(get_product_ids(id_category))), id_category))