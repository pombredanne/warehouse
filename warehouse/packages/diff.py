from warehouse.packages.models import Project, Version, File


def projects(current):
    to_yank = Project.query.filter(~Project.name.in_(current))
    to_yank.update({"yanked": True}, synchronize_session=False)


def versions(project, current):
    # Use different logic if there are any current versions to provide
    #   a more optimal query
    if current:
        to_yank = Version.query.filter(
                                    Version.project == project,
                                    ~Version.version.in_(current),
                                )
    else:
        to_yank = Version.query.filter(Version.project == project)

    # Actually preform the yank
    to_yank.update({"yanked": True}, synchronize_session=False)


def distributions(version, current):
    # Use different logic if there are any current distributions to provide
    #   a more optimal query
    if current:
        to_yank = File.query.filter(
                                    File.version == version,
                                    ~File.filename.in_(current),
                                )
    else:
        to_yank = File.query.filter(File.version == version)

    # Actually preform the yank
    to_yank.update({"yanked": True}, synchronize_session=False)
