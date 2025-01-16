def initAPI(api):
    global vtapi, Docx2HtmlCommand
    vtapi = api

    class Docx2HtmlCommand(vtapi.Plugin.TextCommand):
        def run(self, this=None):
            print("Works")

# def docxToHtml(this=False):
#     pass
# def htmlToDocx(this=False):
#     pass

# def getHtml(f):
#     saveCommand = vtapi.getCommand("saveFile")
#     if saveCommand:
#         return mammoth.convert_to_html(f).value

# def openLikeHtml(f=[]):
#     if not f:
#         f = vtapi.App.openFileDialog()
#     for file in f:
#         vtapi.getCommand("addTab").get("command")()

# def getDocx(html, f):
#     b = html2docx.html2docx(html, "f")
#     with open(f, "ab") as fp:
#         fp.write(b.getvalue())