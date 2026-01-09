import pytest
import tempfile
import json
from unittest.mock import Mock, patch

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from AIAudioTranscriber.src.transcriber.services.TranscriberService import (
    split_text_into_intervals,
    create_intervals,
    convert_segments_to_phrases,
    transcribe_audio
)
from AIAudioTranscriber.src.transcriber.models.Phrase import Phrase
from AIAudioTranscriber.src.transcriber.models.TranscriptionResult import TranscriptionResult


class TestSplitTextIntoIntervals:
    """Тесты для функции split_text_into_intervals"""

    def test_empty_text(self):
        """Тест с пустым текстом"""
        result = split_text_into_intervals("", 0.0, 10.0, 3.0)
        assert result == []

    def test_single_interval(self):
        """Тест с одним интервалом (длительность меньше interval_duration)"""
        text = "Hello world this is a test"
        result = split_text_into_intervals(text, 0.0, 2.0, 3.0)

        assert len(result) == 1
        assert result[0].start == 0.0
        assert result[0].end == 2.0
        assert result[0].text == text



    def test_intervals_with_remaining_words(self):
        """Тест, когда слова не делятся равномерно"""
        text = "word1 word2 word3 word4"
        result = split_text_into_intervals(text, 0.0, 7.0, 3.0)

        # 7 секунд / 3 секунды = 3 интервала (ceil)
        assert len(result) == 3

        # Проверяем распределение слов
        texts = [phrase.text for phrase in result]
        assert "word1" in texts[0]
        assert "word4" in texts[2]

    def test_interval_boundaries(self):
        """Тест граничных случаев"""
        # Граничный случай: start_time == end_time
        result = split_text_into_intervals("test", 5.0, 5.0, 3.0)
        assert result == []

        # Маленький интервал
        result = split_text_into_intervals("short", 0.0, 0.5, 3.0)
        assert len(result) == 1
        assert result[0].end == 0.5



class TestCreateIntervals:
    """Тесты для функции create_intervals"""

    def test_empty_segments(self):
        """Тест с пустым результатом Whisper"""
        whisper_result = {'segments': []}
        result = create_intervals(whisper_result)
        assert result == []

    def test_single_short_segment(self):
        """Тест с одним коротким сегментом"""
        whisper_result = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 2.0,
                    'text': 'Hello world'
                }
            ]
        }
        result = create_intervals(whisper_result, interval_duration=3.0)

        assert len(result) == 1
        assert result[0].start == 0.0
        assert result[0].end == 2.0
        assert result[0].text == 'Hello world'

    def test_single_long_segment(self):
        """Тест с одним длинным сегментом"""
        whisper_result = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 10.0,
                    'text': 'one two three four five six seven eight nine ten'
                }
            ]
        }
        result = create_intervals(whisper_result, interval_duration=3.0)

        # 10 секунд / 3 секунды = 4 интервала (ceil)
        assert len(result) == 4

        # Проверяем, что все интервалы имеют правильную длительность
        for i, phrase in enumerate(result):
            assert phrase.end - phrase.start <= 3.0 + 0.1  # допуск

    def test_multiple_segments(self):
        """Тест с несколькими сегментами"""
        whisper_result = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 2.5,
                    'text': 'First segment'
                },
                {
                    'start': 3.0,
                    'end': 8.0,
                    'text': 'Second longer segment that needs splitting'
                },
                {
                    'start': 9.0,
                    'end': 10.0,
                    'text': 'Third segment'
                }
            ]
        }
        result = create_intervals(whisper_result, interval_duration=3.0)

        # Первый сегмент: 1 фраза (короткий)
        # Второй сегмент: (8.0-3.0)/3.0 = 2 интервала
        # Третий сегмент: 1 фраза (короткий)
        assert len(result) == 4

    def test_segment_with_empty_text(self):
        """Тест с сегментом без текста"""
        whisper_result = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 5.0,
                    'text': ''
                },
                {
                    'start': 6.0,
                    'end': 8.0,
                    'text': 'Valid text'
                }
            ]
        }
        result = create_intervals(whisper_result)

        assert len(result) == 1  # только второй сегмент
        assert result[0].text == 'Valid text'

    def test_custom_interval_duration(self):
        """Тест с пользовательской длительностью интервала"""
        whisper_result = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 15.0,
                    'text': 'a b c d e f g h i j k l m n o'
                }
            ]
        }
        result = create_intervals(whisper_result, interval_duration=5.0)

        # 15 секунд / 5 секунд = 3 интервала
        assert len(result) == 3


class TestConvertSegmentsToPhrases:
    """Тесты для функции convert_segments_to_phrases"""

    def test_basic_functionality(self):
        """Базовая проверка"""
        whisper_result = {
            'phrase': [
                {
                    'start': 0.0,
                    'end': 5.0,
                    'text': 'test phrase'
                }
            ]
        }
        result = convert_segments_to_phrases(whisper_result)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Phrase)

    def test_wrapper_function(self):
        """Проверка, что это обертка над create_intervals"""
        whisper_result = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 5.0,
                    'text': 'test'
                }
            ]
        }

        # Результаты должны быть идентичны
        intervals_result = create_intervals(whisper_result)
        phrases_result = convert_segments_to_phrases(whisper_result)

        assert intervals_result == phrases_result


class TestTranscribeAudio:
    """Тесты для функции transcribe_audio"""

    @pytest.fixture
    def sample_audio_file(self):
        """Создает временный аудиофайл для тестирования"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Записываем минимальный WAV заголовок (невалидный для реального использования,
            # но достаточный для тестов существования файла)
            f.write(b'RIFF____WAVEfmt ')  # минимальный заголовок
            f.flush()
            yield f.name

        # Удаляем после теста
        os.unlink(f.name)

    @patch('whisper.load_model')
    def test_successful_transcription(self, mock_load_model, sample_audio_file):
        """Тест успешной транскрибации"""
        # Мокаем модель Whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            'segments': [
                {
                    'start': 0.0,
                    'end': 3.0,
                    'text': 'Hello world'
                },
                {
                    'start': 3.5,
                    'end': 7.0,
                    'text': 'This is a test'
                }
            ]
        }
        mock_load_model.return_value = mock_model

        result = transcribe_audio(sample_audio_file)

        # Проверяем результаты
        assert result is not None
        assert isinstance(result, TranscriptionResult)
        assert hasattr(result, 'phrases')
        assert len(result.phrases) == 2

        # Проверяем первую фразу
        assert result.phrases[0].start == 0.0
        assert result.phrases[0].end == 3.0
        assert result.phrases[0].text == 'Hello world'

        # Проверяем, что модель была вызвана
        mock_load_model.assert_called_once_with("medium")
        mock_model.transcribe.assert_called_once_with(sample_audio_file)

    def test_file_not_found(self):
        """Тест с несуществующим файлом"""
        result = transcribe_audio("/nonexistent/path/file.wav")
        assert result is None

    def test_unsupported_format(self, tmp_path):
        """Тест с неподдерживаемым форматом"""
        unsupported_file = tmp_path / "test.txt"
        unsupported_file.write_text("Not an audio file")

        result = transcribe_audio(str(unsupported_file))
        assert result is None

    @patch('whisper.load_model')
    def test_whisper_exception(self, mock_load_model, sample_audio_file):
        """Тест исключения в Whisper"""
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Whisper error")
        mock_load_model.return_value = mock_model

        result = transcribe_audio(sample_audio_file)
        assert result is None

    @patch('whisper.load_model')
    def test_empty_transcription_result(self, mock_load_model, sample_audio_file):
        """Тест с пустым результатом транскрибации"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {'segments': []}
        mock_load_model.return_value = mock_model

        result = transcribe_audio(sample_audio_file)

        assert result is not None
        assert isinstance(result, TranscriptionResult)
        assert len(result.phrases) == 0

    def test_supported_formats(self, tmp_path):
        """Тест поддержки различных форматов"""
        supported_extensions = ['.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg']

        for ext in supported_extensions:
            test_file = tmp_path / f"test{ext}"
            test_file.write_text("dummy content")

            # Проверяем, что формат не вызывает ValueError
            # (файл невалидный, но должна пройти проверка формата)
            with patch('whisper.load_model'), patch('whisper.load_model.transcribe'):
                try:
                    # Функция не должна падать с ValueError
                    result = transcribe_audio(str(test_file))
                    # Ожидаем None, так как файл невалидный
                    assert result is None or isinstance(result, TranscriptionResult)
                except ValueError as e:
                    if "Неподдерживаемый формат файла" in str(e):
                        pytest.fail(f"Формат {ext} должен поддерживаться")

    @patch('whisper.load_model')
    def test_temp_directory_setup(self, mock_load_model, sample_audio_file):
        """Тест настройки временной директории"""
        mock_model = Mock()
        mock_model.transcribe.return_value = {'segments': []}
        mock_load_model.return_value = mock_model

        # Запоминаем текущее значение TEMP
        old_temp = os.environ.get('TEMP')

        result = transcribe_audio(sample_audio_file)

        # Проверяем, что TEMP был установлен (хотя бы внутри контекста)
        assert result is not None

        # TEMP должен быть восстановлен после вызова
        current_temp = os.environ.get('TEMP')
        assert current_temp == old_temp


class TestIntegration:
    """Интеграционные тесты"""

    def test_phrase_model_serialization(self):
        """Тест сериализации модели Phrase"""
        phrase = Phrase(
            start=1.5,
            end=3.0,
            text="Test phrase"
        )

        # Проверяем сериализацию в dict
        phrase_dict = phrase.model_dump()
        assert phrase_dict['start'] == 1.5
        assert phrase_dict['end'] == 3.0
        assert phrase_dict['text'] == "Test phrase"

        # Проверяем сериализацию в JSON
        phrase_json = phrase.model_dump_json()
        parsed = json.loads(phrase_json)
        assert parsed['start'] == 1.5

    def test_transcription_result_model(self):
        """Тест модели TranscriptionResult"""
        phrases = [
            Phrase(start=0.0, end=2.0, text="First"),
            Phrase(start=2.0, end=4.0, text="Second")
        ]

        result = TranscriptionResult(phrases=phrases)

        assert len(result.phrases) == 2
        assert result.phrases[0].text == "First"
        assert result.phrases[1].text == "Second"

        # Проверяем сериализацию
        result_dict = result.model_dump()
        assert 'phrases' in result_dict
        assert len(result_dict['phrases']) == 2


