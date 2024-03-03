import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import random
import json
import os
import base64
class GoogleSheetsClient:
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.authorized = False  # Add an authorized flag
        self.creds = self._get_credentials()
        self.service = self._build_service()
        if self.creds and self.creds.valid:
            self.authorized = True  # Set to True after successful authorization


    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    def _get_credentials(self):
        creds = None
        token_path = 'token.json'  # Path where the token will be stored

        # Try to load saved credentials
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)

        # If there are no valid saved creds, start the flow
        if not creds or not creds.valid:
            if 'GOOGLE_CREDENTIALS_BASE64' in os.environ:
                base64_credentials = os.environ['GOOGLE_CREDENTIALS_BASE64']
                decoded_credentials = base64.b64decode(base64_credentials).decode('utf-8')
                credentials_dict = json.loads(decoded_credentials)

                flow = InstalledAppFlow.from_client_config(credentials_dict, self.SCOPES)
                creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

        if not creds or not creds.valid:
            raise Exception("No valid credentials provided.")

        return creds

    def _build_service(self):
        return build("sheets", "v4", credentials=self.creds)

    def get_values(self, range_name, type=str, max_retries=5, maximum_backoff=64):
        """Fetches values from a specified range in the initialized spreadsheet with exponential backoff."""
        print(f"Fetching values from range: {range_name}")
        n = 0  # Initial retry count
        while n <= max_retries:
            try:
                sheet = self.service.spreadsheets()
                result = sheet.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name
                ).execute()
                raw_values = result.get("values", [])

                # Convert values based on the specified type
                converted_values = self.convert_values(raw_values, type)

                return converted_values

            except HttpError as err:
                print(f"Attempt {n + 1} failed with error: {err}")
                if n == max_retries:
                    print("Maximum retry limit reached. Aborting...")
                    return None
                sleep_time = min((2 ** n) + random.randint(0, 1000) / 1000, maximum_backoff)
                print(f"Waiting {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
                n += 1  # Increment retry count

    @staticmethod
    def convert_values(raw_values, type):
        """Converts raw values to specified type."""
        converted_values = []
        for row in raw_values:
            converted_row = []
            for value in row:
                if value == "":
                    converted_row.append(None)
                else:
                    try:
                        converted_row.append(type(value))
                    except ValueError:
                        # In case conversion fails, append the original value
                        converted_row.append(value)
            converted_values.append(converted_row)
        return converted_values

    def get_cols(self, range_name, value_type=str):
        """Fetches values from a single column specified range and returns a flat 1D array.

        Args:
            range_name: A string representing the range to fetch values from.
            value_type: The type to convert the values into. Default is str.

        Returns:
            A flat list of values from the specified single column range, converted to the specified type.
            Returns None if the range is not a single column.
        """
        # Use get_values to fetch the range
        values_2d = self.get_values(range_name, value_type)

        # Check if the range represents a single column
        if ':' in range_name:
            start_col, end_col = range_name.replace('$', '').split(':')
            if start_col[0] == end_col[0]:  # Check if the start and end columns are the same
                # Flatten the 2D array into a 1D array
                flat_list = [item for sublist in values_2d for item in sublist if item is not None]
                return flat_list
            else:
                print("The range is not a single column.")
                return None
        else:
            # If range_name does not contain ':', it's assumed to be a single cell or entire column
            flat_list = [item for sublist in values_2d for item in sublist if item is not None]
            return flat_list

# Example usage
