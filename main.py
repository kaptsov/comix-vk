import shutil
import requests
import os
from dotenv import load_dotenv
import random
import time

UPLOAD_TIMER = 10


class VKError(requests.HTTPError):
    pass


def create_dirs(*args):
    for directory in args:
        os.makedirs(directory, exist_ok=True)


def download_image(url, full_image_name):

    response = requests.get(url)
    response.raise_for_status()

    with open(full_image_name, 'wb') as file:
        file.write(response.content)


def download_comix(pic_num):

    response = requests.get(f'https://xkcd.com/{pic_num}/info.0.json')
    response.raise_for_status()

    pic_data = response.json()
    img_link = pic_data['img']
    img_name = pic_data['safe_title']
    img_comment = pic_data['alt']
    download_image(img_link, f'comix/{img_name}.png')
    return img_comment, img_name


def get_album_info(access_token, user_id, group_id):

    url = 'https://api.vk.com/method/'
    method = 'photos.getWallUploadServer'
    params = {
        'access_token': access_token,
        'v': '5.131',
        'user_id': user_id,
        'group_id': group_id
    }

    response = requests.get(f'{url}{method}', params=params)
    response.raise_for_status()

    upload_data = response.json()['response']
    album_id = str(upload_data['album_id'])[1:]
    upload_url = upload_data['upload_url']
    return upload_data, album_id, upload_url


def upload_photo(img_name, upload_url):

    with open(f'comix/{img_name}.png', 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
    save_data = response.json()
    server = save_data['server']
    photo = save_data['photo']
    photo_hash = save_data['hash']
    return server, photo, photo_hash


def get_media_id(access_token,
                 photo, server, photo_hash, group_id, img_comment):

    url = 'https://api.vk.com/method/'
    method = 'photos.saveWallPhoto'
    params = {
        'access_token': access_token,
        'photo': photo,
        'server': server,
        'hash': photo_hash,
        'group_id': group_id,
        'v': '5.131',
        'caption': img_comment
    }
    response = requests.post(f'{url}{method}', params=params)
    response.raise_for_status()

    save_data = response.json()['response'][0]
    media_id = save_data['id']
    owner_id = save_data['owner_id']
    return media_id, owner_id


def post_to_vk(group_id, owner_id, media_id, access_token):

    url = 'https://api.vk.com/method/'
    method = 'wall.post'
    params = {
        'access_token': access_token,
        'v': '5.131',
        'owner_id': f'-{group_id}',

        'from_group': 1,
        'attachments': f'photo{owner_id}_{media_id}',
        'message': img_comment
    }
    response = requests.get(f'{url}{method}', params=params)
    response.raise_for_status()


if __name__ == '__main__':

    load_dotenv()

    vk_id = os.getenv("VK_ID")
    access_token = os.getenv("ACCESS_TOKEN")
    group_id = os.getenv("GROUP_ID")
    user_id = os.getenv("USER_ID")

    response = requests.get('https://xkcd.com/614/info.0.json')
    response.raise_for_status()
    total_pics = response.json()['num']

    for upload_count in range(total_pics):

        comix_dir = "comix/"
        create_dirs(comix_dir)
        pic_num = random.randint(1, total_pics)

        try:
            img_comment, img_name = download_comix(pic_num)
            upload_data, album_id, upload_url = get_album_info(
                                                                access_token,
                                                                user_id,
                                                                group_id
                                                                )
            server, photo, photo_hash = upload_photo(img_name, upload_url)
            media_id, owner_id = get_media_id(
                                            access_token, photo, server,
                                            photo_hash, group_id, img_comment
                                            )
            post_to_vk(group_id, owner_id, media_id, access_token)
        except VKError as error:
            print('Ошибка обращения к API vk.com')
        except requests.exceptions.HTTPError:
            print('Ошибка обработки HTTP запроса, запустите скрипт еще раз')
        finally:
            shutil.rmtree('comix')

        time.sleep(UPLOAD_TIMER)

