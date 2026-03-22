import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Если измените SCOPES, удалите token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveUploader:
    """Класс для загрузки файлов в Google Drive"""

    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Аутентификация и создание сервиса Google Drive"""
        creds = None

        # Файл token.pickle хранит токены пользователя
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # Если нет действительных credentials, просим пользователя войти
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Сохраняем credentials для следующего раза
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('drive', 'v3', credentials=creds)
        print("✅ Google Drive авторизация успешна")

    def upload_file(self, file_path, file_name=None):
        """
        Загружает файл в Google Drive
        Возвращает: (file_id, web_view_link, download_link)
        """
        if not file_name:
            file_name = os.path.basename(file_path)

        # Метаданные файла
        file_metadata = {
            'name': file_name,
            'parents': ['root']
        }

        # Загружаем файл
        media = MediaFileUpload(
            file_path,
            mimetype='video/mp4',
            resumable=True
        )

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Делаем файл доступным по ссылке
        self.service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        # Получаем прямую ссылку на скачивание
        file_id = file['id']
        download_link = f"https://drive.google.com/uc?export=download&id={file_id}"

        return file_id, file['webViewLink'], download_link

    def delete_file(self, file_id):
        """Удаляет файл из Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Ошибка удаления файла: {e}")
            return False


# Создаём глобальный экземпляр
gdrive_uploader = GoogleDriveUploader()