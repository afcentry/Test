#-*- coding:utf-8 -*-
from .Subdomain.sublist3r import ScanSubdomain
import dns.resolver

class DomainIPDiger:
    @staticmethod
    def GetSubdomain(domain,verbose=True,threads=200,enable_bruteforce=False):
        domain=domain.strip()
        domains=[]
        try:
            domains=ScanSubdomain(domain=domain,verbose=verbose,threads=threads,enable_bruteforce=enable_bruteforce)
        except Exception as e:
            print ("[!]Get subdomains error:{}".format(e))
        str_result = domain + ">" + "|".join(domains)
        return str_result

    @staticmethod
    def GetIp(domain):
        domain=domain.strip()
        address=[]
        try:
            host_domain=dns.resolver.query(domain)
            for i in host_domain.response.answer:
                for j in i.items:
                    address.append(j.address)
        except Exception as e:
            print ("[!]Get subdomains error:{}".format(e))
        str_result=domain+">"+"|".join(address)
        return str_result


