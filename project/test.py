import gzip
import string
import urllib.request

import functions as fn
import libs.xmltodict as xmltodict


SELECTED_ENVIRONMENT = 'workstation-product-environment'
additional_groups = ['core', 'critical-path-base', 'critical-path-apps', 'critical-path-gnome']
ignore_optional = True
ignore_default = False
dl_list = set()
packages_list = set()
provided = set()
required = set()
base_url = 'https://dl.fedoraproject.org/pub/fedora/linux/releases/36/Everything/x86_64/os/'
work_dir = r'C:/Users/trapp/repoooooo/'
repomd_file = 'repodata/repomd.xml'
fn.mkdir(work_dir + 'Packages/')
fn.mkdir(work_dir + 'repodata/')
for char in list(string.ascii_lowercase + string.digits):
    fn.mkdir(work_dir + 'Packages/' + char)


def main():
    comps_file = ''
    primary_file = ''
    urllib.request.urlretrieve(base_url + repomd_file, work_dir + repomd_file)
    with open(work_dir + repomd_file, 'r', encoding='iso-8859-1') as repo:
        repomd = xmltodict.parse(repo.read())
        for entry in repomd['repomd']['data']:
            urllib.request.urlretrieve(base_url + entry['location']['@href'], work_dir + entry['location']['@href'])
            if entry['@type'] == 'group':
                comps_file = entry['location']['@href']
            if entry['@type'] == 'primary':
                primary_file = entry['location']['@href']

    with open(work_dir + comps_file, 'r', encoding='iso-8859-1') as comps:
        repo_dict = xmltodict.parse(comps.read())
        environments = repo_dict['comps']['environment']
        for environment in environments:
            if environment['id'] != SELECTED_ENVIRONMENT: continue
            for group_id in environment['grouplist']['groupid']:
                for group in repo_dict['comps']['group']:
                    if group['id'] not in [group_id] + additional_groups: continue
                    packages_list.update(get_packages_in_group(group))

    with gzip.open(work_dir + primary_file, 'rt', encoding='utf-8') as f:
        repo_dict = xmltodict.parse(f.read())
        packages = repo_dict['metadata']['package']
        for package in packages:
            if package['name'] in packages_list:
                add_package(packages, package, provided, required, dl_list)


def add_package(all_packages, package, provided: set, required: set, dl_list: set):
    # refresh the required list
    print(packages_list)
    print('provided: ', provided)
    print('required: ', required)
    required = set([require for require in required if require not in provided])

    dl_list.add(package['location']['@href'])
    for provide in package['format']['rpm:provides']['rpm:entry']:
        provided.add(provide['@name'])
        if provide['@name'] not in required: continue
        required.remove(provide['@name'])
    for require in package['format']['rpm:requires']['rpm:entry']:
        if require['@name'] in provided: continue
        required.add(require['@name'])

    if not required: return True
    for package in all_packages:
        for provide in package['format']['rpm:provides']['rpm:entry']:
            if provide['@name'] not in required: continue
            add_package(all_packages, package, provided=provided, required=required, dl_list=dl_list)
            break
        if not required: return True
main()

'''        for dl in dl_list:
            urllib.request.urlretrieve(base_url + dl, r'C:/Users/trapp/repoooooo/' + dl)
'''


def get_packages_in_group(group):
    packages = set()
    for package in group['packagelist']['packagereq']:
        if ignore_optional and package['@type'] == 'optional': continue
        if ignore_default and package['@type'] == 'default': continue
        packages.add(package['#text'])
    return packages
