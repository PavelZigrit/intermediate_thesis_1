import logging

from vk_photos_to_ya_disk import VkLoader


ya_token_file = "ya_token.txt"
vk_token_file = "vk_token.txt"
vk_id = 0
vk_username = None

with open(ya_token_file) as f:
    ya_token = f.read()
with open(vk_token_file) as f:
    vk_token = f.read()


if __name__ == "__main__":
    loader = VkLoader(ya_token, vk_token)
    loader.upload_vk_profile_photos_to_ya_disk(vk_id, 15, vk_username)
    logging.info("End")
