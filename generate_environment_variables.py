#!/usr/bin/env python

import os
import argparse
import codecs

CATKIN_MARKER_FILE = '.catkin'

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate environment variables for the rosjava maven environment.')
    cmd_group = parser.add_mutually_exclusive_group()
    cmd_group.add_argument('-d', '--maven-deployment-repository', action='store_true', help='Return the current devel workspace maven directory.')
    cmd_group.add_argument('-r', '--maven-repository', action='store_true', help='The url to the external ros maven repository.')
    cmd_group.add_argument('-m', '--maven-path', action='store_true', help='Generate maven path across all chained workspcaes.')
    cmd_group.add_argument('-g', '--gradle-user-home', action='store_true', help='Generate the local gradle user home in the current devel workspace (share/gradle).')
    cmd_group.add_argument('-l', '--local-maven-repository', action='store_true', help='Generate the local maven cache in the current devel workspace (share/maven).')
    cmd_group.add_argument("-s", '--create-maven-settings', action='store_true', help='Generate maven settings.xml for the current devel workspace.')
    args = parser.parse_args()
    return args

MAVEN_HEADER="""
	<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
    http://maven.apache.org/xsd/settings-1.0.0.xsd">
		<profiles>
			<profile>
				<id>catkin</id>
				<activation>
					<activeByDefault>true</activeByDefault>
				</activation>
				<repositories>
"""

MAVEN_FOOTER="""
				</repositories>
			</profile>
		</profiles>
	</settings>
"""


def get_repository_xml(id, path):

	if path.startswith("/"):
		path = "file://" + path

	return """
		<repository>
			<id>{id}</id>
			<name>{id}</name>
			<url>{url}</url>
			<layout>default</layout>
			<releases>
				<updatePolicy>always</updatePolicy>
				<enabled>true</enabled>
			</releases>
			<snapshots>
				<updatePolicy>always</updatePolicy>
				<enabled>true</enabled>
			</snapshots>
		</repository>
		""".format(
			url=path,
			id=id,
		)

def get_repositories_xml():
	maven_paths = generate_maven_path()
	settings = ""
	for id, repo, in enumerate(maven_paths.split(":")):
		settings += get_repository_xml(id,repo)
	return settings

def get_workspaces(environ):
    '''
    Based on CMAKE_PREFIX_PATH return all catkin workspaces.
    '''
    # get all cmake prefix paths
    env_name = 'CMAKE_PREFIX_PATH'
    value = environ[env_name] if env_name in environ else ''
    paths = [path for path in value.split(os.pathsep) if path]
    # dont remove non-workspace paths
    workspaces = [path.replace(' ', '\ ') for path in paths]
    return workspaces

def get_environment_variable(environ, key):
    var = None
    try:
        var = environ[key]
    except KeyError:
        pass
    if var == '':
        var = None
    return var

def generate_maven_path():
    new_maven_paths = [os.path.join(path, 'share', 'repository') for path in workspaces] #TODO: make configurable!
    maven_paths = get_environment_variable(environment_variables, 'ROS_MAVEN_PATH')
    if maven_paths is None:
        maven_paths = new_maven_paths
    else:
        maven_paths = maven_paths.split(os.pathsep)
        common_paths = [p for p in maven_paths if p in new_maven_paths]
        if common_paths:
            maven_paths = new_maven_paths

    return os.pathsep.join(maven_paths)

if __name__ == '__main__':
    args = parse_arguments()
    environment_variables = dict(os.environ)
    workspaces = get_workspaces(environment_variables)
    if args.maven_deployment_repository:
        repo = get_environment_variable(environment_variables, 'ROS_MAVEN_DEPLOYMENT_REPOSITORY')
        if repo is None:
            repo = os.path.join(workspaces[0], 'share', 'repository') #TODO: make configurable!
        else:
            if repo in [os.path.join(w, 'share', 'repository') for w in workspaces]: #TODO: make configurable!
                repo = os.path.join(workspaces[0], 'share', 'repository') #TODO: make configurable!
        print(repo)
    elif args.maven_repository:
        repo = get_environment_variable(environment_variables, 'ROS_MAVEN_REPOSITORY')
        if repo is None:
            repo = 'https://mvn.cit-ec.de/nexus/content/repositories/releases/'
        print(repo)
    elif args.maven_path:
        print(generate_maven_path())
    elif args.gradle_user_home:
        home = get_environment_variable(environment_variables, 'GRADLE_USER_HOME')
        if home is None:
            home = os.path.join(workspaces[0], 'share', 'gradle')
        else:
            if home in [os.path.join(w, 'share', 'gradle') for w in workspaces]:
                home = os.path.join(workspaces[0], 'share', 'gradle')
        print(home)
    elif args.local_maven_repository:
        home = get_environment_variable(environment_variables, 'MAVEN_USER_LOCAL_REPOSITORY') #TODO research key
        if home is None:
            home = os.path.join(workspaces[0], 'share', 'maven')
        else:
            if home in [os.path.join(w, 'share', 'maven') for w in workspaces]:
                home = os.path.join(workspaces[0], 'share', 'maven')
        print(home)
    elif args.create_maven_settings:
        s = (MAVEN_HEADER + get_repositories_xml() + MAVEN_FOOTER)
        print(repr(s)[1:-1])
    else:
        print("Nothing to see here - please provide one of the valid command switches.")
