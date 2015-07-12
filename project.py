import sublime, sublime_plugin 	#这是sublime插件必须要引入的两个库
import os
import glob

import threading, time

from .SideBarAPI import SideBarItem, SideBarSelection

def Window():
	return sublime.active_window()

BASE_PATH = os.path.abspath(os.path.dirname(__file__))

TMLP_DIR = 'templates'

PACKAGE_NAME = 'project'

class ProjectCommand(sublime_plugin.WindowCommand):
	def run(self, paths = [], new = False):
		import functools
		Window().run_command('hide_panel');
		items = []
		for item in SideBarSelection(paths).getSelectedDirectoriesOrDirnames():
			items.append(item.path())
		view = Window().show_input_panel("请输入项目名:", 
			items[0] + '\\', 
			self.on_done, 
			None, None)
		view.sel().clear()
		view.sel().add(sublime.Region(view.size(), view.size()))
	def on_done(self, result):
		key = 'new-project'+str(time.time())
		if result.endswith('\\') == False:
			result = ''.join([result, '\\'])
		print(result.endswith('\\'))
		PasteThread([result], 'False', 'True', 'False', key).start()

class PasteThread(threading.Thread):
	def __init__(self, paths = [], in_parent = 'False', test = 'True', replace = 'False', key = ''):
		self.paths = paths
		self.in_parent = in_parent
		self.test = test
		self.replace = replace
		self.key = key
		threading.Thread.__init__(self)

	def run(self):
		PasteCommand2(sublime_plugin.WindowCommand).run(self.paths, self.in_parent, self.test, self.replace, self.key)

class PasteCommand2(sublime_plugin.WindowCommand):
	def run(self, paths = [], in_parent = 'False', test = 'True', replace = 'False', key = ''):
		#window_set_status(key, 'Pasting…')
		items = []

		for item in SideBarSelection([BASE_PATH + '\\' + TMLP_DIR + '\\']).getSelectedItemsWithoutChildItems():
			items.append(item.path())

		copy = "\n".join(items)
		already_exists_paths = []

		if SideBarSelection(paths).len() > 0:
			if in_parent == 'False':
				location = SideBarSelection(paths).getSelectedItems()[0].path()
			else:
				location = SideBarSelection(paths).getSelectedDirectoriesOrDirnames()[0].dirname()

			if os.path.isdir(location) == False:
				location = SideBarItem(os.path.dirname(location), True)
			else:
				location = SideBarItem(location, True)

			if copy != '':
				copy = copy.split("\n")
				for path in copy:
					path = SideBarItem(path, os.path.isdir(path))
					new  = os.path.join(location.path())
					if test == 'True' and os.path.exists(new):
						already_exists_paths.append(new)
					elif test == 'False':
						if os.path.exists(new) and replace == 'False':
							pass
						else:
							try:
								if not path.copy(new, replace == 'True'):
									#window_set_status(key, '')
									sublime.error_message("Unable to copy and paste, destination exists.")
									return
							except:
								#window_set_status(key, '')
								sublime.error_message("Unable to copy:\n\n"+path.path()+"\n\nto\n\n"+new)
								return

			if test == 'True' and len(already_exists_paths):
				self.confirm(paths, in_parent, already_exists_paths, key)
			elif test == 'True' and not len(already_exists_paths):
				PasteThread(paths, in_parent, 'False', 'False', key).start();
			elif test == 'False':
				window_set_status(key, '')
		else:
			window_set_status(key, '')

	def confirm(self, paths, in_parent, data, key):
		import functools
		window = sublime.active_window()
		window.show_input_panel("BUG!", '', '', None, None)
		window.run_command('hide_panel');

		yes = []
		yes.append('Yes, 替换现有项目:');
		for item in data:
			yes.append(SideBarItem(item, os.path.isdir(item)).pathWithoutProject())

		no = []
		no.append('No');
		no.append('不做替换');

		while len(no) != len(yes):
			no.append('ST3 BUG');

		window.show_quick_panel([yes, no], functools.partial(self.on_done, paths, in_parent, key))

	def on_done(self, paths, in_parent, key, result):
		#window_set_status(key, '')
		if result != -1:
			if result == 0:
				PasteThread(paths, in_parent, 'False', 'True', key).start()
			else:
				PasteThread(paths, in_parent, 'False', 'False', key).start()

def window_set_status(key, name =''):
	for window in sublime.windows():
		for view in window.views():
			view.set_status('NewProject-'+key, name)