# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

	config.vm.define "bfapi" do |bfapi|
		bfapi.vm.box = "ubuntu/trusty64"
		bfapi.vm.hostname = "bf-api.dev"
		bfapi.vm.provision :shell, path: "vagrant/vagrant-bootstrap.sh"
		bfapi.vm.network "forwarded_port", guest: 5000, host: 5001
		bfapi.vm.network "forwarded_port", guest: 5432, host: 5432
		bfapi.vm.network "forwarded_port", guest: 8080, host: 8089
		bfapi.vm.provider "virtualbox" do |vb|
	      vb.customize [
	      	"modifyvm", :id,
	      	"--natdnshostresolver1", "on",
	      	"--memory", "2048"
	      ]
		end
	end
	
end