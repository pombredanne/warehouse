from django.core.management.base import BaseCommand, CommandError

from optparse import make_option


class Command(BaseCommand):
    args = "<service>"
    help = "Starts the specified service"

    option_list = BaseCommand.option_list + (
        make_option(
            "--debug",
            action="store_true",
            dest="debug",
            default=False
        ),
    )

    def handle(self, service_name="http", **options):
        from warehouse.services import http

        services = {
            "http": http.WarehouseHTTPServer,
        }

        try:
            service_class = services[service_name]
        except KeyError:
            raise CommandError("%r is not a valid service" % service_name)

        service = service_class(
            debug=options["debug"],
        )

        print "Running service: %r" % service_name
        service.run()
