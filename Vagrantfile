# coding: utf-8
# -*- mode: ruby -*-
# vi: set ft=ruby :

linux_os = "ubuntu/bionic64"   # Ubuntu 18.04
bridge_if = "en0: Wi-Fi (Wireless)"

vm_spec = [
  { name: "node3", cpu: 1, memory: 1536,
    box: linux_os,
    private_ip: "172.20.1.33",
    #public_ip: "192.168.1.93",
    storage: [100], playbook: "install_node.yaml",
    comment: "Ceph node #3" },

  { name: "node2", cpu: 1, memory: 1536,
    box: linux_os,
    private_ip: "172.20.1.32",
    #public_ip: "192.168.1.92",
    storage: [100], playbook: "install_node.yaml",
    comment: "Ceph node #2" },

  { name: "node1", cpu: 1, memory: 1536,
    box: linux_os,
    private_ip: "172.20.1.31",
    public_ip: "192.168.1.91",
    storage: [100], playbook: "install_node.yaml",
    comment: "Ceph node #1" },
]


Vagrant.configure("2") do |config|
  vm_spec.each do |spec|
    config.vm.define spec[:name] do |v|
      v.vm.box = spec[:box]
      v.vm.hostname = spec[:name]
      v.vm.network :private_network,ip: spec[:private_ip]
      if !( spec[:public_ip].nil? )
        v.vm.network :public_network,ip:  spec[:public_ip], bridge: bridge_if
      end	     
      v.vm.provider "virtualbox" do |vbox|
        vbox.gui = false
        vbox.cpus = spec[:cpu]
        vbox.memory = spec[:memory]
        i = 1
        spec[:storage].each do |vol|
          vdisk = "vdisks/sd-" + spec[:name] + "-" + i.to_s + ".vdi"

          if not File.exist?(vdisk) then
            vbox.customize [
              'createmedium', 'disk',
              '--filename', vdisk,
              '--format', 'VDI',
              '--size', vol * 1024 ]
          end
          vbox.customize [
            'storageattach', :id,
            '--storagectl', 'SCSI',
            '--port', 1 + i,
            '--device', 0,
            '--type', 'hdd',
            '--medium', vdisk]
          i = i + 1
          
        end
      end
      v.vm.synced_folder ".", "/vagrant", owner: "vagrant",
                            group: "vagrant", mount_options: ["dmode=700", "fmode=700"]

      v.vm.provision "ansible_local" do |ansible|
        ansible.playbook       = "playbooks/" + spec[:playbook]
        ansible.install_mode   = "pip"
        ansible.version        = "2.9.6"    
        ansible.verbose        = false
        ansible.install        = true
        ansible.limit          = spec[:name] 
        ansible.inventory_path = "playbooks/hosts"
      end
    
      # v.vm.provision "shell", inline: <<-SHELL
      #   apt-get update
      #   apt-get install -y apache2
      # SHELL
    end
  end
end
