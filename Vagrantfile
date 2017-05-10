# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

	config.vm.define "bfapi" do |bfapi|
		bfapi.vm.box = "ubuntu/trusty64"
		bfapi.vm.hostname = "bf-api.dev"

		bfapi.vm.provision :shell, path: "vagrant/vagrant-bootstrap.sh"
		if ENV["FAKE_GEOAXIS"] == "true"
			bfapi.vm.provision :shell, path: "vagrant/vagrant-bootstrap-fake-geoaxis.sh"
			bfapi.vm.provision :shell, run: "always", path: "vagrant/vagrant-start-fake-geoaxis.sh"
		else
			bfapi.vm.provision :shell, run: "always", path: "vagrant/vagrant-start.sh"
		end

		# Note: 5000 and 5001 must be passed through unshifted since they need
		# to be accessible at localhost:5000 and localhost:5001 in both host and guest
		bfapi.vm.network "forwarded_port", guest: 5000, host: 5000
		bfapi.vm.network "forwarded_port", guest: 5001, host: 5001
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
