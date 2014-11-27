import sublime, sublime_plugin

class JumpToMethodCommand(sublime_plugin.TextCommand):
    FLAG_manualPath         = True
    PATH_basePathRepository = "/home/bogdana/workspace/avangate.secure.git/"
    PATH_sourceRepository   = "secure"

    def prepareFolders(self):
        if (self.FLAG_manualPath):
            project_data = sublime.active_window().project_data()
            project_folder = project_data['folders']
            project_folder = [{'path': self.PATH_basePathRepository, 'follow_symlinks': True}]
        else:
            project_data = sublime.active_window().project_data()
            project_folder = project_data['folders']

        return project_folder

    def run(self, edit):
        project_folder = self.prepareFolders()
        
        itemMethodExtractor                         = MethodExtractor()
        itemMethodExtractor.FLAG_manualPath         = self.FLAG_manualPath
        itemMethodExtractor.PATH_basePathRepository = self.PATH_basePathRepository
        itemMethodExtractor.PATH_sourceRepository   = self.PATH_sourceRepository

        for (item) in project_folder:
            itemMethodExtractor.traverseFolders(item['path'])

        itemMethodExtractor.processMain()
