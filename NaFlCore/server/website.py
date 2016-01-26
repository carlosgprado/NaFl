#
# webby thing
#


import tornado.ioloop
import tornado.web

from database import crash_database

ADDRESS = '127.0.0.1'
PORT = 8888


class FuzzBoard():

    def __init__(self):
        """
        This is a poor man's dashboard :)
        """
        self.crash_information = None


    def retrieve_crash_information(self):
        """
        Read the database
        """
        rows = crash_database.retrieve_crashes()

        return rows


    def generate_table(self):
        """
        This generates HTML code representing a table
        """

        if not self.crash_information:
            self.crash_information = self.retrieve_crash_information()

        crashes = []
        for row in self.crash_information:
            crashes.append(row)

        crashes.sort(key = lambda t: t[5])

        table_html = """
            <table class="table table-striped table-condensed">
                  <thead>
                  <tr>
                      <th>Index</th>
                      <th>Node</th>
                      <th>Victim</th>
                      <th>CPU</th>
                      <th>Event Name</th>
                      <th>IP</th>
                      <th>Stack Trace</th>
                      <th>Crash Label</th>
                      <th>Exploitability</th>
                      <th>Filename</th>
                  </tr>
              </thead>
              <tbody>
        """

        for idx, n, v, c, ev, ip, st, cl, exp, fname in crashes:
            # HACKY
            row = """<tr>
                <td>%d</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>0x%08x</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td><a href="crashes/%s">%s</a></td>
                </tr>""" % (idx, n, v, c, ev, int(ip), st, cl, exp, fname, fname)

            table_html += row

        table_html += '</tbody></table>'

        return table_html


    def generate_website(self):

        html_code = """
        <!DOCTYPE html>
        <html>
        <head>
        <title>NaFl Dashboard</title>
        <link rel="stylesheet" href="static/bootstrap.min.css">
        </head>
        <body>
        <div style="width:auto; margin-right:10px; margin-top:20px; float:left">
        %s
        </div>
        </body>
        </html>
        """ % self.generate_table()

        return html_code


class MainHandler(tornado.web.RequestHandler):
    """
    This generates the (static) dashboard webpage
    """
    def get(self):
        dashboard = FuzzBoard()
        self.write(dashboard.generate_website())


def main():

    print "=" * 80
    print "Starting the web server..."
    print "=" * 80

    application = tornado.web.Application([
        (r'/', MainHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static'}),
        (r"/crashes/(.*)", tornado.web.StaticFileHandler, {'path': 'crashes'}),
        ])

    application.listen(PORT, address = ADDRESS)
    tornado.ioloop.IOLoop.instance().start()


################################################################
if __name__ == '__main__':
    main()
