-- phpMyAdmin SQL Dump
-- version 4.9.5deb2
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Сен 12 2020 г., 10:09
-- Версия сервера: 10.3.23-MariaDB-1
-- Версия PHP: 7.4.5

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `bot`
--

-- --------------------------------------------------------

--
-- Структура таблицы `admins`
--

CREATE TABLE `admins` (
  `user_id` bigint(20) NOT NULL,
  `which_question_edit` int(11) NOT NULL DEFAULT 0,
  `state` tinyint(16) NOT NULL DEFAULT 0,
  `is_admin_edit` tinyint(1) NOT NULL DEFAULT 0,
  `tmp` bigint(20) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Дамп данных таблицы `admins`
--

INSERT INTO `admins` (`user_id`, `which_question_edit`, `state`, `is_admin_edit`, `tmp`) VALUES
(613595894, 0, 0, 1, 0);

-- --------------------------------------------------------

--
-- Структура таблицы `adtab`
--

CREATE TABLE `adtab` (
  `id` int(11) NOT NULL,
  `channel_id` bigint(20) NOT NULL DEFAULT 0,
  `link` tinytext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Структура таблицы `bot_settings`
--

CREATE TABLE `bot_settings` (
  `id` int(11) NOT NULL,
  `data` int(11) DEFAULT NULL,
  `date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Дамп данных таблицы `bot_settings`
--

INSERT INTO `bot_settings` (`id`, `data`, `date`) VALUES
(1, NULL, '2020-09-11 00:00:00'),
(2, NULL, NULL),
(3, NULL, '2020-09-11 00:00:00');

-- --------------------------------------------------------

--
-- Структура таблицы `cache`
--

CREATE TABLE `cache` (
  `question_number` int(11) NOT NULL DEFAULT 0,
  `user_id` bigint(20) NOT NULL,
  `time_left` time NOT NULL DEFAULT '00:00:00',
  `time_message_id` int(11) NOT NULL DEFAULT 0,
  `can_continue` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Структура таблицы `questions`
--

CREATE TABLE `questions` (
  `number` int(11) NOT NULL,
  `is_right_answer` tinyint(1) NOT NULL DEFAULT 0,
  `data` text NOT NULL DEFAULT '',
  `type` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Дамп данных таблицы `questions`
--

INSERT INTO `questions` (`number`, `is_right_answer`, `data`, `type`) VALUES
(1, 0, 'Правильный ответ - а', 1),
(1, 1, 'а', 0),
(1, 0, 'б', 0),
(1, 0, 'в', 0),
(2, 0, 'Правильный ответ - б', 1),
(2, 0, 'а', 0),
(2, 1, 'б', 0),
(2, 0, 'в', 0),
(3, 0, 'Правильный ответ - в', 1),
(3, 0, 'а', 0),
(3, 0, 'б', 0),
(3, 1, 'в', 0),
(4, 0, 'Тут просто тестовый вопрос', 1),
(4, 0, 'а', 0),
(4, 0, 'б', 0),
(4, 0, 'в', 0),
(4, 1, 'Правильный ответ', 0);

-- --------------------------------------------------------

--
-- Структура таблицы `statistic`
--

CREATE TABLE `statistic` (
  `str_id` tinytext NOT NULL,
  `value` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Дамп данных таблицы `statistic`
--

INSERT INTO `statistic` (`str_id`, `value`) VALUES
('new users', 2),
('q:1', 2),
('q:2', 1),
('q:3', 1),
('q:4', 0);

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `user_id` bigint(20) NOT NULL,
  `balance` int(11) NOT NULL DEFAULT 0,
  `state` tinyint(10) NOT NULL DEFAULT 0,
  `is_do_victorine` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`user_id`, `balance`, `state`, `is_do_victorine`) VALUES
(613595894, 100, 0, 1);

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `adtab`
--
ALTER TABLE `adtab`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `bot_settings`
--
ALTER TABLE `bot_settings`
  ADD PRIMARY KEY (`id`);

--
-- Индексы таблицы `cache`
--
ALTER TABLE `cache`
  ADD PRIMARY KEY (`user_id`);

--
-- Индексы таблицы `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `adtab`
--
ALTER TABLE `adtab`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
