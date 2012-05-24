#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.pardir)
import socket, random

from conf import conf

def _parse_cluster_config(config_path):
    """function to parse configuration about cluster's information

    @param config_path path of cluster's information config file
    @return dictionary of cluster(id_name) from IP
    >>> ret = _parse_cluster_config("./test_data/slaves_test.conf")
    >>> assert(ret['192.168.11.1'] == 'local')
    >>> assert(ret['133.11.117.36'] == 'hongo')
    >>> assert(len(ret) == 4)
    """
    f = open(config_path, 'r')
    ret_cluster_dict = {}
    cluster_name = ''
    while True:
        buf = f.readline()

        if buf == '':  # End of file
            break
        elif buf[:1] == '#': # Comment
            continue
        elif buf[:1] == ' ' or buf[:1] == '\t':
            buf = buf.lstrip(' ')
            buf = buf.lstrip('\t')
            if cluster_name != '':
                try:
                    host = buf.rstrip("\n")
                    ip = socket.gethostbyname(host)
                    ret_cluster_dict[ip] = cluster_name
                except socket.error, e:
                    MogamiLog.error("We cannot resolve address of %s, so %s is not added to nodes." % (host, host))
            else:
                DDDFSLog.error("** config file format is invalid **")
                sys.exit(1)
        else:
            cluster_name = buf.rstrip('\n')
    return ret_cluster_dict

class NodeInfo(object):
    TYPE_META = 0
    TYPE_DATA = 1
    TYPE_FS = 2
    def __init__(self, ip, cluster):
        self.ip = ip
        self.cluster = cluster

class DataNodeInfo(NodeInfo):
    def __init__(self, ip, cluster):
        NodeInfo.__init__(self, ip, cluster)
        self.type = NodeInfo.TYPE_DATA

class ClientNodeInfo(NodeInfo):
    def __init__(self, ip, cluster):
        NodeInfo.__init__(self, ip, cluster)
        self.type = NodeInfo.TYPE_FS

class ClusterNodesInfo(object):
    def __init__(self, cluster):
        self.cluster = cluster
        self.ip_list = []
        self.nodes_num = 0

    def add_node(self, ip):
        self.ip_list.append(ip)
        self.nodes_num += 1

class DDDFSNodesInfo(object):
    def __init__(self, config_path):
        self.cluster_dict = _parse_cluster_config(config_path)

        self.meta_ip = ''
        self.data_ip_list = []
        self.client_ip_list = []

        self.data_cluster_dict = {}    # e.g.) {'hongo': ClusterNodesInfo}
        self.client_cluster_dict = {}

    def add_node(self, ip, node_type):
        if node_type == NodeInfo.TYPE_META:
            """this type will maybe be not used
            """
            self.meta_ip = ip
        elif node_type == NodeInfo.TYPE_DATA:
            try:
                cluster = self.cluster_dict[ip]
            except KeyError, e:
                return -1
            node_info = DataNodeInfo(ip, cluster)
            self.data_ip_list.append(ip)
            if not self.data_cluster_dict.has_key(cluster):
                self.data_cluster_dict[cluster] = ClusterNodesInfo(cluster)
            self.data_cluster_dict[cluster].add_node(ip)
        else:
            try:
                cluster = self.cluster_dict[ip]
            except KeyError, e:
                return -1
            node_info = ClientNodeInfo(ip, cluster)
            self.client_ip_list.append(ip)
            if not self.client_cluster_dict.has_key(cluster):
                self.client_cluster_dict[cluster] = ClusterNodesInfo(cluster)
            self.client_cluster_dict[cluster].add_node(ip)

        return 0

    def choose_random_from_datanodes(self, remv_nodes):
        """choose one of data servers at random.

        @return 
        """
        candidates_list = []
        for ip in self.data_ip_list:
            if ip not in remv_nodes:
                candidates_list.append(ip)
        if len(candidates_list) == 0:
            return None
        return candidates_list[random.randint(0, len(candidates_list) - 1)]

    def choose_datanode_in_cluster(self, cluster, remv_nodes):
        candidates_list = []
        for ip in self.data_cluster_dict[cluster].ip_list:
            if ip not in remv_nodes:
                candidates_list.append(ip)
                
        if len(candidates_list) == 0:
            return None
        return candidates_list[random.randint(0, len(candidates_list) - 1)]

    def calcRTT(self, from_ip, to_ip):
        """
        """
        if self.cluster_dict[from_ip] == self.cluster_dict[to_ip]:
            return conf.rtt_lan
        else:
            return conf.rtt_wan

if __name__ == '__main__':
    import doctest
    doctest.testmod()
