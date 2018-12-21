#! -*- coding:utf-8 -*-
import sys
from sys import stdin
from sys import stdout

debug=False

class Node:
    """
    node in cycle(contract)
    self.weight===weight of arc from the previous node in cycle
    """
    def __init__(self,i,w):
        self.id,self.weight=i,w

    def __str__(self):
        return "(%d,%f)" % (self.id,self.weight)
    __repr__ = __str__

class Contract:
    """
    contract of nodes in cycle
    """
    def __init__(self,nid,node_list,graph):
        self.nid=nid    # contract id
        self.node_l=[] # node list, 有序
        self.node_d={}  # node dict, 查询用
        for i,n in enumerate(node_list):
            self.node_d[n]=i
            node_i=n
            node_w=graph[node_list[i-1]][n]
            self.node_l.append(Node(node_i,node_w))
        self.in_node={} # in_node[v]=c
        self.out_node={} # out_node[v]=c

    def contains(self,node):
        return node in self.node_d

    def nlist(self,head):
        """
        return: sequence of contract nodes, <head> as the first node
        """
        hidx=self.node_d[head]
        return self.node_l[hidx:]+self.node_l[:hidx]

    def __str__(self):
        return "--- Contract %d ---\nnode_l: %s\nnode_d: %s\nin_node: %s\nout_node: %s\n- - - - - -" % (
                self.nid, str(self.node_l), str(self.node_d), str(self.in_node), str(self.out_node))
    __repr__ = __str__

def _log(s):
    if debug:
        stdout.write(s)

def _reverse(g):
    """
    return: reversed graph
    """
    rg={}
    for s in g:
        for d in g[s]:
            if s==d:
                continue
            if d not in rg:
                rg[d]={}
            rg[d][s]=g[s][d]
    return rg

def _cycle(rg):
    """
    check if reversed directed graph has cycle
    return: cycle(list of nodes sequence of the first detected cycle)
            or None if no cycle exists
    """
    visited={}  # global visited nodes
    for d in rg:
        if d in visited:
            continue
        d_visited={d:1} # visited nodes in this loop
        s,w=rg[d].items()[0]
        # note: len(rg[d])=1
        while s in rg and s not in d_visited and s not in visited:
            d_visited[s]=1
            s,w=rg[s].items()[0]
        if s in d_visited:
            # s in the cycle
            cycle=[s]
            n,w=rg[s].items()[0]
            while n!=s:
                cycle.append(n)
                n,w=rg[n].items()[0]
            cycle.reverse()
            return cycle
        # merge d_visited into visited
        _log("Cycle(): d:%d, d_visited: %s\n"%(d,str(d_visited.keys())))
        for n in d_visited:
            visited[n]=1
    return None

def _tree(g,rg,contracts):
    """
    construct a tree from reversed graph and contract dict

    return: tree and reversed tree
    """
    cids=sorted(contracts.keys())   # 按顺序逐层展开
    for cid in cids:
        _log("_tree(): cid=%d\n%s"%(cid, _g2str(g)))
        contract=contracts[cid]
        n_in,w=rg[cid].items()[0]
        head=contract.in_node[n_in]
        cnodes=contract.nlist(head)
        wi=g[n_in].pop(cid)
        for i,cnode in enumerate(cnodes):
            if n_in not in g:
                g[n_in]={}
            if i==0: # head
                g[n_in][cnode.id]=wi+cnode.weight
            else:
                g[n_in][cnode.id]=cnode.weight
            n_in=cnode.id

        if cid in g:
            for n_out in g[cid]:
                cnode=contract.out_node[n_out]
                if cnode not in g:
                    g[cnode]={}
                g[cnode][n_out]=g[cid][n_out]
            g.pop(cid)

        rg=_reverse(g)

    return g,rg

def _merge(g,rg,cycle,contracts):
    """
    merge graph and cycle, record cycle info into contracts
    return: merged graph
    """
    _log("CYCLE: \n%s\n"%(str(cycle)))

    cid=-(len(contracts)+1)
    contract=Contract(cid,cycle,g)

    ng={}   # merged graph
    for src in g:
        for dst in g[src]:
            if src==dst:
                continue
            if contract.contains(src):
                if contract.contains(dst):
                    continue
                else: # update out_node
                    if cid not in ng:
                        ng[cid]={}
                    if dst not in ng[cid] or ng[cid][dst]<g[src][dst]:
                        ng[cid][dst]=g[src][dst]
                        contract.out_node[dst]=src
            else:
                if contract.contains(dst): # update in_node
                    weight=g[src][dst]-contract.node_l[contract.node_d[dst]].weight
                    if src not in ng:
                        ng[src]={}
                    if cid not in ng[src] or ng[src][cid]<weight:
                        ng[src][cid]=weight
                        contract.in_node[src]=dst
                else:   # copy
                    if src not in ng:
                        ng[src]={}
                    ng[src][dst]=g[src][dst]
    _log("CONTRACT: \n"+str(contract)+"\n")

    contracts[cid]=contract
    return ng

def mst(g,root):
    """
    g: original directed graph, g[src][dst]=weight
    src,dst: node id, integers >=0
    root:   root node id

    return: max span tree and reversed mst
    """
    contracts={}    # contracts of nodes, key=contract id(interger<0), value=Contract instance

    while True:
        rg = _reverse(g)
        if root in rg:
            rg.pop(root)
        _log("G: \n%sRG: \n%s"%(_g2str(g),_g2str(rg)))

        # find max incident arc for each node
        mx_rg={}
        for d in rg:
            mx,mx_s=-float('inf'),None
            for s in rg[d]:
                if rg[d][s]>mx:
                    mx,mx_s=rg[d][s],s
            if d not in mx_rg:
                mx_rg[d]={}
            mx_rg[d][mx_s]=mx
        _log("MX_RG: \n%s"%(_g2str(mx_rg)))

        # check if mx_rg has cycle
        cycle=_cycle(mx_rg)

        if cycle==None:
            mx_g=_reverse(mx_rg)
            return _tree(mx_g,mx_rg,contracts)

        g=_merge(g,rg,cycle,contracts)

def _g2str(g):
    res=""
    for s in g:
        for d in g[s]:
            res+="%d\t%d\t%f\n"%(s,d,g[s][d])
    return res

if __name__=="__main__":
    g={}
    line=stdin.readline()
    ln=0
    while line:
        g[ln]={}
        f=line.strip().split(" ")
        for i in range(0,len(f)):
            g[ln][i]=float(f[i])
        line=stdin.readline()
        ln+=1
    t,rt=mst(g,0)

    stdout.write("Max Span Tree:\n")
    stdout.write(_g2str(rt))
