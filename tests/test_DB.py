
from src.DB import DB

import unittest
from unittest import mock


class Test_DB(unittest.TestCase):


    @mock.patch('src.DB.requests')
    def test_init_with_valid_bearer_and_default_db(self, mocker):
        # # Arrange
        # # with mock.patch('src.DB.requests') as mock_requests:

        # #     mock_config = mocker.patch('config.db', 'http://example.com/')
        # bearer_token = "valid_token"
    
        # # Act
        # db_instance = DB("test_bearer")

        # # db_instance = DB(bearer=bearer_token)
    
        # # Assert
        # self.assertEqual(db_instance.bearer, bearer_token)
        # self.assertEqual(db_instance.db, "http://example.com")

        bearer_token = "test_bearer"
        db_instance = DB(bearer_token)
        self.assertEqual(db_instance.bearer, bearer_token)
        self.assertEqual(db_instance.db, "http://zooprocess.imev-mer.fr:8081/v1")



    def test_init_with_empty_bearer_raises_error(self):
        # Arrange
        empty_bearer = ""
    
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            DB(bearer=empty_bearer)
    
        self.assertEqual(str(context.exception), "Bearer token is required")




    # Successfully retrieves JSON data from a valid URL
    def test_get_retrieves_json_data_from_valid_url(self):
        # Arrange
        from unittest.mock import patch, MagicMock
        from src.DB import DB
    
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
    
        with patch('requests.get', return_value=mock_response) as mock_get:
            db = DB("test_token")
            # db.bearer = "test_token"
            db.db = "http://test-url.com"
        
            # Act
            result = db.get("/test-path")
        
            # Assert
            mock_get.assert_called_once_with(
                "http://test-url.com/test-path", 
                headers={"Authorization": "Bearer test_token", "Content-Type": "application/json"}
            )
            self.assertEqual(result, {"key": "value"})

    # Handles empty URL parameter
    @mock.patch('requests.get')
    def test_get_handles_empty_url_parameter(self, mock_get):
        db = DB("test_token", "http://test-url.com")  # Remove trailing slash here
        db.get("")
        mock_get.assert_called_once_with(
            "http://test-url.com",  # Remove trailing slash here
            headers={"Authorization": "Bearer test_token", "Content-Type": "application/json"}
        )