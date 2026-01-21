"""
Unit tests for OpenAI API integration in analyse_strava.py
Tests the generer_feedback_coach() function with mocked API calls
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyse_strava import generer_feedback_coach


class TestGenererFeedbackCoach:
    """Tests for generer_feedback_coach() function with OpenAI API mocks"""

    @pytest.fixture
    def sample_stats(self):
        """Sample training statistics for testing"""
        return {
            'volume_total': 12.5,
            'volume_course': 6.0,
            'volume_ski': 4.5,
            'nb_activites': 8,
            'duree_moyenne': 1.56,
            'distance_totale': 95.3,
            'semaines_surcharge': 1
        }

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response structure"""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "Wow, 12.5 heures d'entraînement! On dirait que quelqu'un a découvert que les canapés ne mènent nulle part. Continue comme ça, champion, et tu finiras peut-être par rattraper ta motivation!"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        return mock_response

    def test_successful_feedback_generation(self, sample_stats, mock_openai_response):
        """Test successful feedback generation with valid API response"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            # Mock st.secrets
            mock_st.secrets = {"OPENAI_API_KEY": "test-api-key-12345"}

            # Mock OpenAI client and response
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            # Call function
            result = generer_feedback_coach(sample_stats)

            # Assertions
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0
            assert "12.5" in result or "entraînement" in result

            # Verify OpenAI was called correctly
            mock_openai_class.assert_called_once_with(api_key="test-api-key-12345")
            mock_client.chat.completions.create.assert_called_once()

            # Check the call arguments
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs['model'] == 'gpt-5-nano'
            assert len(call_args.kwargs['messages']) == 2
            assert call_args.kwargs['messages'][0]['role'] == 'system'
            assert call_args.kwargs['messages'][1]['role'] == 'user'
            assert 'sarcastique' in call_args.kwargs['messages'][0]['content']

    def test_feedback_with_minimal_stats(self, mock_openai_response):
        """Test feedback generation with minimal statistics"""
        minimal_stats = {
            'volume_total': 2.0,
            'volume_course': 1.0,
            'volume_ski': 0.5,
            'nb_activites': 2,
            'duree_moyenne': 1.0,
            'semaines_surcharge': 0
        }

        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(minimal_stats)

            assert result is not None
            # Verify the stats were included in the prompt
            call_args = mock_client.chat.completions.create.call_args
            user_message = call_args.kwargs['messages'][1]['content']
            assert '2.00 heures' in user_message  # volume_total
            assert 'Nombre d\'activités : 2' in user_message

    def test_feedback_with_missing_distance(self, mock_openai_response):
        """Test feedback generation when distance_totale is missing"""
        stats_no_distance = {
            'volume_total': 5.0,
            'volume_course': 3.0,
            'volume_ski': 2.0,
            'nb_activites': 5,
            'duree_moyenne': 1.0,
            'semaines_surcharge': 0
            # distance_totale is missing
        }

        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(stats_no_distance)

            assert result is not None
            # Verify default distance of 0 is used
            call_args = mock_client.chat.completions.create.call_args
            user_message = call_args.kwargs['messages'][1]['content']
            assert 'Distance totale : 0.00 km' in user_message

    def test_api_key_passed_correctly(self, sample_stats, mock_openai_response):
        """Test that API key from secrets is passed correctly"""
        test_api_key = "sk-proj-custom-test-key-xyz123"

        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": test_api_key}
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(sample_stats)

            assert result is not None
            mock_openai_class.assert_called_once_with(api_key=test_api_key)

    def test_openai_api_error(self, sample_stats):
        """Test handling of OpenAI API errors"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API rate limit exceeded")
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(sample_stats)

            # Should return None on error
            assert result is None

    def test_openai_authentication_error(self, sample_stats):
        """Test handling of authentication errors"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "invalid-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(sample_stats)

            assert result is None

    def test_openai_network_error(self, sample_stats):
        """Test handling of network errors"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("Connection timeout")
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(sample_stats)

            assert result is None

    def test_empty_response_content(self, sample_stats):
        """Test handling of empty response content"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}

            # Mock response with empty content
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = ""
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(sample_stats)

            # Should return empty string
            assert result == ""

    def test_prompt_includes_all_stats(self, sample_stats):
        """Test that the prompt includes all required statistics"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}

            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Feedback test"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            generer_feedback_coach(sample_stats)

            # Verify the prompt contains all stats
            call_args = mock_client.chat.completions.create.call_args
            user_message = call_args.kwargs['messages'][1]['content']

            assert '12.50 heures' in user_message  # volume_total
            assert '6.00 heures' in user_message   # volume_course (appears in prompt)
            assert '4.50 heures' in user_message   # volume_ski (appears in prompt)
            assert 'Nombre d\'activités : 8' in user_message
            assert '1.56 heures' in user_message   # duree_moyenne
            assert '95.30 km' in user_message      # distance_totale
            assert 'Semaines en surcharge (>10h) : 1' in user_message

    def test_system_message_content(self, sample_stats, mock_openai_response):
        """Test that system message has correct coaching personality"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            generer_feedback_coach(sample_stats)

            call_args = mock_client.chat.completions.create.call_args
            system_message = call_args.kwargs['messages'][0]['content']

            # Check for key personality traits
            assert 'coach' in system_message.lower()
            assert 'sarcastique' in system_message.lower()
            assert 'drôle' in system_message.lower()
            assert 'humour' in system_message.lower()

    def test_max_tokens_parameter(self, sample_stats, mock_openai_response):
        """Test that max_completion_tokens parameter is set correctly"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            generer_feedback_coach(sample_stats)

            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs['max_completion_tokens'] == 5000

    def test_high_volume_stats(self, mock_openai_response):
        """Test feedback generation with high training volume"""
        high_volume_stats = {
            'volume_total': 25.0,
            'volume_course': 15.0,
            'volume_ski': 10.0,
            'nb_activites': 20,
            'duree_moyenne': 1.25,
            'distance_totale': 250.0,
            'semaines_surcharge': 4
        }

        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(high_volume_stats)

            assert result is not None
            # Verify high volume is in prompt
            call_args = mock_client.chat.completions.create.call_args
            user_message = call_args.kwargs['messages'][1]['content']
            assert '25.00 heures' in user_message
            assert 'Semaines en surcharge (>10h) : 4' in user_message

    def test_zero_stats(self, mock_openai_response):
        """Test feedback generation with zero/minimal activity"""
        zero_stats = {
            'volume_total': 0.0,
            'volume_course': 0.0,
            'volume_ski': 0.0,
            'nb_activites': 0,
            'duree_moyenne': 0.0,
            'distance_totale': 0.0,
            'semaines_surcharge': 0
        }

        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(zero_stats)

            assert result is not None
            # Verify zeros are in prompt
            call_args = mock_client.chat.completions.create.call_args
            user_message = call_args.kwargs['messages'][1]['content']
            assert '0.00 heures' in user_message
            assert 'Nombre d\'activités : 0' in user_message

    def test_client_initialization_error(self, sample_stats):
        """Test handling of OpenAI client initialization errors

        The OpenAI client initialization is now inside the try-except block,
        so initialization errors are caught and the function returns None.
        """
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}
            mock_openai_class.side_effect = Exception("Failed to initialize OpenAI client")

            result = generer_feedback_coach(sample_stats)

            # Client initialization errors are now caught, should return None
            assert result is None

    def test_missing_api_key_in_secrets(self, sample_stats):
        """Test handling when API key is missing from st.secrets"""
        with patch('analyse_strava.st') as mock_st:

            # Mock secrets without OPENAI_API_KEY
            mock_st.secrets = {}

            result = generer_feedback_coach(sample_stats)

            # Should return None when API key is missing
            assert result is None

    def test_response_format(self, sample_stats):
        """Test that response format is correctly extracted"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}

            # Mock response with specific feedback text
            expected_feedback = "Tu cours comme une gazelle asthmatique! Mais bon, c'est déjà mieux qu'un escargot en grève."
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = expected_feedback
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(sample_stats)

            assert result == expected_feedback

    def test_unicode_in_response(self, sample_stats):
        """Test handling of Unicode characters in response"""
        with patch('analyse_strava.st') as mock_st, \
             patch('analyse_strava.OpenAI') as mock_openai_class:

            mock_st.secrets = {"OPENAI_API_KEY": "test-key"}

            # Mock response with Unicode characters
            unicode_feedback = "Bravo! 🎉 Tu as couru 95 km! 🏃‍♂️💨 Continue comme ça, champion! 🏆"
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = unicode_feedback
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client

            result = generer_feedback_coach(sample_stats)

            assert result == unicode_feedback
            assert "🎉" in result
            assert "🏃‍♂️" in result
