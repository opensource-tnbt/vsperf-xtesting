virtualenv xtesting
. xtesting/bin/activate
pip install ansible
ansible-galaxy install collivier.xtesting
ansible-playbook site.yml
deactivate
rm -r xtesting
