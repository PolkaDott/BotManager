from ..templates.super_plugin import SuperPlugin, admin_only
import os, datetime, time
from .. import crons
from ..templates.super_view import SuperView
from typing import Callable


def remember_request(func):
    """Decorator for admin panel. Remembers last command, then it may be used to repeat this.
    Must be BELOW @admin_only"""
    def wrapper(self, view, context):
        self.last_exec = (func, view, context)
        func(self, view, context)
    return wrapper


class AdminPanel(SuperPlugin):
    last_exec: tuple[Callable, SuperView, dict] = ()

    def __init__(self, bot):
        super().__init__(bot)

    @admin_only
    @remember_request
    def reboot(self, view: SuperView, context):
        """Reboot the core bot. """
        view.report('Начался перезапуск...')
        self.log('Program is rebooting by admin')
        res_path = os.path.join(os.getcwd(), 'logs')
        os.system(f'nohup python3 main.py @chatbotstation_core@ '
                  f'start -MS > {res_path}/core_launch_log.txt 2>&1 &')
        print(res_path)
        time.sleep(10)
        # Класс Communicator другой вьюшки должен насильно закрыть этот процесс.
        # Если не закроет, значит что-то пошло не так
        self.log('Program was not rebooted')
        view.report("Core isn't rebooted")

    @admin_only
    @remember_request
    def exit(self, view: SuperView, context):
        self._bot.communicator.close()
        self.log('Program is suspended by admin')
        view.report('Core stopped.')
        os._exit(1)

    @admin_only
    @remember_request
    def update_module(self, view: SuperView, context):
        module: str = context['message']
        if len(module) == 0:
            view.reply('Нельзя обновить все плагины сразу. Нужно указать название определенного', context)
            return
        updated = self._bot.plugin_manager.update_plugin(module)
        if updated > 0:
            view.reply(f'Плагин {module} обновлён в оперативной памяти', context)
            return
        try:
            updated = self._bot.views_manager.update_view(module)
        except Exception as e:
            view.reply(str(e), context)
            return
        if updated == 1:
            view.reply(f'Вьюшка {module} обновлена в оперативной памяти, но она не запущена', context)
        elif updated == 2:
            view.reply(f'Вьюшка {module} обновлена в оперативной памяти полностью', context)
        elif updated == 0:
            view.reply('Не найдено модулей с таким именем', context)

    @admin_only
    def repeat_cmd(self, view: SuperView, context: dict):
        if self.last_exec:
            func, view, context = self.last_exec
            func(self, view, context)
        else:
            view.reply('There is no command in memory', context)

    def common_status(self):
        status = ''
        dt = datetime.datetime.utcnow()-self.start_time
        if dt.days == 0:
            if dt.seconds < 60:
                dt = str(dt.seconds) + " секунд"
            elif dt.seconds < 60*60:
                dt = str(dt.seconds//60) + " минут"
            else:
                dt = str(dt.seconds//60//60) + " часов"
        elif dt.days < 7:
            dt = str(dt.days) + " дней"
        elif dt.days < 30:
            dt = str(dt.days // 7) + " недель"
        elif dt.days < 365:
            dt = str(dt.days//30) + " месяцев"
        else: dt = str(dt.days//365) + " лет"
        status += f'С запуска бота прошло {dt}\n'
        status += self._get_tasks_status()
        self.sender.send(self.user_id, status)

    def _get_tasks_status(self):
        tasks = crons.get('../resources/config.ini')
        respond = ''
        all_tasks = []
        for x in self.bot.plugin_manager.plugins:
            for j in x.tasks:
                all_tasks.append(j)
        for t in all_tasks:
            if t in tasks:
                respond += '- ' + t +' активен&#128640;\n'
        for t in all_tasks:
            if t not in tasks:
                respond += '- ' + t +' неактивен&#9898;\n'
        return respond

    def show_tasks(self):
        tasks = crons.get('../resources/config.ini')
        respond = ''
        all_tasks = []
        for x in self.bot.plugin_manager.plugins:
            for j in x.tasks:
                all_tasks.append(j)
        for t in all_tasks:
            if t in tasks:
                respond += '- ' + t +' активен&#128640;\n'
        for t in all_tasks:
            if t not in tasks:
                respond += '- ' + t +' неактивен&#9898;\n'
        self.sender.send(self.user_id, respond)

    def show_logs(self):
        if self.message == '':
            path_to_logs = './../logs/'
            filename = path_to_logs + sorted(os.listdir(path_to_logs))[-1]
            with open(filename, 'r') as file:
                self.sender.send(self.user_id, file.read()[-12000:])
            return
        ''' ##############
        app = None
        for a in self.bot.apps:
            if a.name == self.message:
                app = a
        if app == None:
            self.log('No app with such name %s' % self.message)
            self.sender.send(self.user_id, f'Нет приложения с названием "{self.message}"')
            return
        folder = app.folder
        path_to_logs = f'./../apps/{folder}/logs/'
        filename = path_to_logs + sorted(os.listdir(path_to_logs))[-1]
        with open(filename, 'r', encoding='utf-8') as file:
            self.sender.send(self.user_id, file.read()[-12000:])
        '''

    def auto_commands(self):
        answer = ''
        for x in self.bot.plugins:
            answer += '- '+x.__class__.__name__+'\n'
            if len(x.cmds) > 0:
                answer += 'COMMANDS: '
                answer += ', '.join(list(x.cmds.keys()))
                answer += '\n'
            if len(x.prefixes) > 0:
                answer += 'PREFIXES: '
                answer += ', '.join(list(x.prefixes.keys()))
                answer += '\n'

        self.sender.send(self.user_id, answer)

    def schedule_task(self):
        task = self.message
        plugin = None
        for plug in self.bot.plugins:
            if task in plug.tasks:
                plugin = plug
        if plugin == None:
            all_tasks = []
            for plug in self.bot.plugins:
                for x in plug.tasks:
                    all_tasks.append(x)
            self.sender.send(self.user_id, 'Такой задачи нет. Все задачи: ' + ', '.join(all_tasks))
            self.log(f'Unknown task {task} is called')
            return
        delay = plugin.tasks[task][1]
        path = os.path.split(os.getcwd())[0]
        crons.add(plugin.__class__.__name__, task, delay, path)
        self.log(f'Task {task} is scheduled')
        self.sender.send(self.user_id, 'Задача запущена')

    def unschedule_task(self):
        task = self.message
        plugin = None
        for plug in self.bot.plugins:
            if task in plug.tasks:
                plugin = plug
        if plugin == None:
            all_tasks = []
            for plug in self.bot.plugins:
                for x in plug.tasks:
                    all_tasks.append(x)
            self.sender.send(self.user_id, 'Такой задачи нет. Все задачи: ' + ', '.join(all_tasks))
            self.log(f'Unknown task {task} is called')
            return
        path = os.path.split(os.getcwd())[0]
        crons.remove(plugin.__class__.__name__, task, path)
        self.log(f'Task {task} is unscheduled')
        self.sender.send(self.user_id, 'Задача удалена')

    prefixes = {
        "logs": show_logs,
        "логи": show_logs,
        "start": schedule_task,
        "stop": unschedule_task,
        "update": update_module,
    }
    cmds = {
        "status": common_status,
        "tasks": show_tasks,
        "задачи": show_tasks,
        "выход": exit,
        "exit": exit,
        "выключить": exit,
        "stop": exit,
        "status": common_status,
        "перезагрузить": reboot,
        "перезапустить": reboot,
        "reboot": reboot,
        "ребут": reboot,
        ".": repeat_cmd,
    }