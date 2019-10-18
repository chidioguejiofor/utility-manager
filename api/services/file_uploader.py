import os
import logging
import cloudinary.uploader
import api.models as models
from celery_config import celery_app, app
from settings import db


class FileUploader:

    @staticmethod
    def _update_model_image(model_name, model_id, upload_response):
        getattr(models,
                model_name).query.filter_by(id=model_id).update(
            dict(image_public_id=upload_response['public_id'],
                 image_url=upload_response['secure_url']))

    @staticmethod
    @celery_app.task(name='upload-file-to-cloudinary')
    def upload_file(model_id, model_name, filename=None, image_public_id=None):
        """Uploads file to cloudinary Asynchronously using celery

        Args:
            model_id (str): the id of the model where the image_url would be saved
            model_name (str): the name of the model in api.models
            filename (str): the string name of the file that has been cached temporarily
            image_public_id(str, optional): If provided an attempt would be made to remove the
                existing image in cloudinary.

        Returns:
            str: "Success" when the operation succeeds or "Failure" otherwise

        """
        error = False
        try:
            upload_response = cloudinary.uploader.upload(filename)
        except Exception as e:
            error = True
            logging.exception(e)
            upload_response = None

        if os.path.isfile(filename):
            print('-------Removing File-----')
            print(filename)
            os.remove(filename)

        if error is True:
            return "Failure"
        if image_public_id and upload_response:
            cloudinary.uploader.destroy(image_public_id)

        if os.getenv('FLASK_ENV') == 'testing':
            return FileUploader._update_model_image(model_name, model_id, upload_response)
        else:
            with app.app_context():
                return FileUploader._update_model_image(model_name, model_id, upload_response)

