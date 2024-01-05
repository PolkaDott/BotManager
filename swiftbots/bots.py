from traceback import format_exc
from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from swiftbots.types import (IView, IController, IMessageHandler, ILogger, ILoggerFactory,
                             ITask)


class Bot:
    """A storage of controllers and views"""

    name: str
    __logger: ILogger = None
    __db_session_maker: Optional[async_sessionmaker[AsyncSession]] = None

    view_class: type[IView] | None
    controller_classes: list[type[IController]]
    task_classes: list[type[ITask]] | None
    message_handler_class: Optional[type[IMessageHandler]] | None

    view: IView | None
    controllers: list[IController]
    tasks: list[ITask] | None
    message_handler: IMessageHandler | None

    @property
    def logger(self) -> ILogger:
        return self.__logger

    @property
    def db_session_maker(self) -> async_sessionmaker[AsyncSession]:
        return self.__db_session_maker

    def __init__(self, controller_classes: list[type[IController]], view_class: type[IView] | None,
                 task_classes: list[type[ITask]] | None, message_handler_class: type[IMessageHandler] | None,
                 logger_factory: ILoggerFactory | None, name: str, db_session_maker: async_sessionmaker | None):
        self.view_class = view_class
        self.controller_classes = controller_classes
        self.task_classes = task_classes
        self.message_handler_class = message_handler_class
        self.name = name
        self.__logger = logger_factory.get_logger()
        self.__logger.bot_name = self.name
        self.__db_session_maker = db_session_maker


def _set_views(bots: list[Bot]) -> None:
    """
    Instantiate and set views
    """
    for bot in bots:
        if bot.view_class:
            bot.view = bot.view_class()
            bot.view.init(bot)


def _set_controllers(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot controllers, each one must be singleton
    """
    controller_memory: list[IController] = []
    for bot in bots:
        controllers_to_add: list[IController] = []
        controller_types = bot.controller_classes

        for controller_type in controller_types:
            found_instances = list(filter(lambda inst: controller_type is inst, controller_memory))
            if len(found_instances) == 1:
                controller_instance = found_instances[0]
            elif len(found_instances) == 0:
                controller_instance = controller_type()
                controller_instance.init(bot.db_session_maker)
                controller_memory.append(controller_instance)
            else:
                raise Exception('Invalid algorithm')
            controllers_to_add.append(controller_instance)

        bot.controllers = controllers_to_add


def _set_message_handlers(bots: list[Bot]) -> None:
    """
    Instantiate and set handlers
    """
    for bot in bots:
        if bot.view_class:
            if bot.message_handler_class is None:
                bot.message_handler_class = bot.view_class.default_message_handler_class
            bot.message_handler = bot.message_handler_class(bot.controllers, bot.logger)


def _set_tasks(bots: list[Bot]) -> None:
    """
    Instantiate and set tasks
    """
    for bot in bots:
        if bot.task_classes:
            task_classes = bot.task_classes
            tasks = []
            for task_class in task_classes:
                task = task_class()
                task.init(bot.logger, bot.db_session_maker)
                tasks.append(task)
            bot.tasks = tasks


def _instantiate_in_bots(bots: list[Bot]) -> None:
    """
    Instantiate and set to the bot instances, each controller must be singleton
    """
    _set_views(bots)
    _set_controllers(bots)
    _set_message_handlers(bots)


async def close_bot_async(bot: Bot):
    """
    Call `_close` method of bot to softly close all connections
    """
    try:
        await bot.view.soft_close_async()
        if bot.tasks:
            for task in bot.tasks:
                await task.soft_close_async()
    except Exception as e:
        await bot.logger.error_async(f'Raised an exception `{e}` when a bot closing method called:\n{format_exc()}')
