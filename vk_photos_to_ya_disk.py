import time
import requests
import os
import json
from datetime import datetime
import logging

logging.basicConfig(filename="Log.log", filemode="w", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class YaUploader:
    def __init__(self, ya_token):
        self.ya_token = ya_token

    def upload(self, file_path):
        response = requests.put(self.get_upload_link(file_path), data=open(file_path, "rb"), timeout=5)
        if response.status_code == 201:
            return "Success"

    def get_path_for_vk_photos(self, vk_id, username):
        if vk_id == 0 and username == "owner":
            path = "vk_app_owner_photos_reserve"
        elif vk_id == 0:
            path = f"vk_{username}_photos_reserve"
        elif username == "owner":
            path = f"vk_{vk_id}_photos_reserve"
        else:
            path = f"vk_{username}_{vk_id}_photos_reserve"
        return path

    def get_headers(self):
        return {"Content-type": "application/json", "Authorization": f"OAuth {self.ya_token}"}

    def get_upload_link(self, file_path):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        params = {"path": os.path.basename(file_path), "overwrite": "true"}
        response = requests.get(url, params=params, headers=self.get_headers(), timeout=5)
        time.sleep(0.3)
        return response.json()["href"]

    def ya_disk_create_folder(self, vk_id, username):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        logging.info(f"Getting path for new folder on Yandex Disk")
        params = {"path": "/" + self.get_path_for_vk_photos(vk_id, username)}
        logging.info(f"Path created: {params['path']}")
        logging.info(f"Creating folder for Yandex Disk")
        resp = requests.put(url, params=params, headers=self.get_headers(), timeout=5)
        if resp.status_code == 201:
            logging.info(f"Status code: {resp.status_code}, folder created")
        elif resp.status_code == 409:
            logging.warning(f"Status code: {resp.status_code}, folder already exists")
        else:
            logging.error(f"Status code: {resp.status_code}")
        time.sleep(0.3)
        return resp.json()

    def ya_disk_upload_from_link(self, file_url, file_name, vk_id, username):
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        params = {"url": file_url,
                  "path": "/" + self.get_path_for_vk_photos(vk_id, username) + "/" + file_name
                  }
        resp = requests.post(url, params=params, headers=self.get_headers(), timeout=5)
        if resp.status_code == 202:
            logging.info(f"Status code:{resp.status_code}, file {file_name} uploaded")
        else:
            logging.error(f"Error, status code{resp.status_code}")
        time.sleep(0.3)
        return


class VkLoader(YaUploader):
    Vk_url = "https://api.vk.com/method/"

    def __init__(self, ya_token, vk_token):
        super().__init__(ya_token)
        self.vk_token = vk_token
        self.params = {
            "access_token": self.vk_token,
            "v": "5.130"
        }

    def get_photo(self, owner_id, count, vk_url=Vk_url):
        url = vk_url + "photos.get"
        photo_params = {
            "album_id": "profile",
            "extended": 1,
            "count": count,
            "photo_sizes": 1
        }
        if owner_id != 0:
            photo_params["owner_id"] = owner_id
            logging.info(f"Getting photos dict for user id: {owner_id}")
        else:
            logging.info(f"Getting photos dict for app owner(id = 0)")
        resp = requests.get(url, params={**self.params, **photo_params}, timeout=5)
        if resp.status_code == 200:
            logging.info(f"Dict recieved, status code: {resp.status_code}")
        else:
            logging.error(f"Error, Status code: {resp.status_code}")
        time.sleep(0.4)
        return resp.json()["response"]["items"]

    def photos_sort(self, vk_id, count):
        photos_list = []
        for photo in self.get_photo(vk_id, count):
            photo_dict = {"likes": photo["likes"]["count"], "date": photo["date"], "size": photo["sizes"][-1]["type"],
                          "url": photo["sizes"][-1]["url"]}
            photos_list.append(photo_dict.copy())
            photo_dict.clear()
        final_photos_list = []
        names_list = []
        for photo in photos_list:
            if photo["likes"] not in names_list:
                photo_dict["file_name"] = photo["likes"]
                names_list += [photo["likes"]]
            else:
                date = str(datetime.fromtimestamp(photo["date"]))
                date = date.replace(" ", "_")
                date = date.replace(":", ".")
                photo_dict["file_name"] = date
            photo_dict["size"] = photo["size"]
            photo_dict["url"] = photo["url"]
            final_photos_list.append(photo_dict.copy())
        names_list.clear()
        logging.info("Original photos dict transformed to list")
        return final_photos_list

    def upload_vk_profile_photos_to_ya_disk(self, vk_id=0, count=10, username=None):
        logging.info("Program started")
        if count > 1000 or count < 0 or type(count) != int:
            logging.error("Wrong input (count type must be int and value >=0 and <=1000)")
            return
        if type(vk_id) != int:
            logging.error("Wrong input (vk_id type must be int)")
            return
        photos_list = self.photos_sort(vk_id, count)
        if username is None:
            username = "owner"
        self.ya_disk_create_folder(vk_id, username)
        logging.info("Started uploading to Yandex Disk")
        for photo in photos_list:
            self.ya_disk_upload_from_link(photo.pop("url"), str(photo["file_name"]) + ".jpg", vk_id, username)
        self.write_to_json(photos_list, vk_id, username)
        return

    def write_to_json(self, photos_list, vk_id, username):
        logging.info("Dumping photos info to json file")
        with open(f"{self.get_path_for_vk_photos(vk_id, username)}.json", "w") as f:
            json.dump({"Photos": photos_list}, f, indent=2)
        logging.info(f"Created file: {self.get_path_for_vk_photos(vk_id, username)}.json")
        return
