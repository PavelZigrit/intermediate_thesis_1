import logging

from vk_photos_to_ya_disk import VkLoader


ya_token = ""
vk_token = "958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008"
vk_id = 552934290


if __name__ == "__main__":
    loader = VkLoader(ya_token, vk_token)
    loader.upload_vk_profile_photos_to_ya_disk(vk_id)
    logging.info("End")
