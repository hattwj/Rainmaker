import random                           #cmd
from string import lowercase, digits,Formatter #cmd rand
from yaml import safe_load              #parser
from pipes import quote                 #cmd
from os.path import abspath,basename    #cmd

from .path import which,current_user    #cmd
from .logger import create              #logging


class RecordScript(object):
    ''' RecordScipt: The active yaml templating dsl ''' 
    def __init__(self,attrs={},depth=2):
        self.log = create(self.__class__.__name__)
        self.attrs=attrs
        self._formatter = Formatter() 
    
    # optionally remove flags from val 
    def remove_flags(self,val):
        for tup in self._formatter.parse(val):
            if not tup[1]:
                continue
            key = tup[1]
            rep_key = "${%s}" % ':'.join([key,tup[2]]) if tup[2] else "${%s}" % key
            val = val.replace(rep_key,'')
        return val

    # add/update attrs dict 
    def attrs_update(self,attrs):
        self.attrs = dict( self.attrs.items()+attrs.items() )
     
    # substitute val template with attrs dict
    def subst(self, val, attrs={},times=7):
        result = val
        has_flags = False
        #print "input: %s" % val
        #print "times: %s" % times
        attrs = dict( self.attrs.items() + attrs.items() )
        # get tuple of values for every key in string        
        for tup in self._formatter.parse(val):
            # next if no flags
            if tup[1] == None:
                continue
            
            #self.log.debug("flag tuple:")
            #self.log.debug(tup)
            
            # process tuple of flags - immutable array -
            has_flags=True
            key = tup[1]
            cmd_key = "__cmd_%s__" % key
            rep_key = "${%s}" % ':'.join([key,tup[2]]) if tup[2] else "${%s}" % key
            rep_val = None

            # get cmd if exists in this class
            cmd = getattr(self,cmd_key) if hasattr(self,cmd_key) else None
            # execute command if one is present and the command
            # doesn't have an override
            if cmd and key not in attrs:
                self.log.debug("cmd: %s" % cmd_key)
                data = safe_load( tup[2] ) if tup[2] else None
                if isinstance(data,dict):
                    rep_val = cmd(attrs,**data)
                elif isinstance(data,list): 
                    rep_val = cmd(attrs,*data)
                elif data != None:
                    rep_val = cmd(attrs,data)
                else:
                    rep_val = cmd(attrs) 
            elif key in attrs:
                rep_val = attrs[key]
            elif key and '.' in key:
                keys = key.split('.')
                rep_val=attrs
                for k in keys:
                    if isinstance(rep_val,list):
                        k=int(k)
                    try:
                        rep_val=rep_val[k]
                    except KeyError:
                        raise KeyError('missing "%s" portion of "%s"' % (k,key) )
                    
            if rep_val==None or not rep_key:
                self.log.warn("subst missing val or key:\n\tval=%s\n\tkey=%s" % (rep_val,rep_key))
                continue
            if isinstance(rep_val,list):
                rep_val = ''.join(rep_val)
            elif rep_val == False:
                rep_val = ''
            #print 'times eol: %s' % times
            result = result.replace(rep_key,str(rep_val),1)
        if times >= 1 and has_flags:
            result = self.subst(result,attrs,times-1)
        else:
            self.log.debug("output: %s" % result)
        return result

    def __cmd_for_each__(self,attrs,key,val,elem_key=None):
        result = []
        xattrs = None
        key = self.subst(key,attrs)
        for elem in attrs[key]:
            # nest elem in dict if elem_key
            elem = {elem_key : elem} if elem_key else elem
            result.append( self.subst(val,elem) )
        return result
    
    def __cmd_quote__(self,attrs,val):
        ''' Quote string'''
        return quote(self.subst(val,attrs))

    def __cmd_yaml__(self,attrs,val):
        ''' return yaml object '''
        return safe_load(val)

    def __cmd_which__(self,attrs,val):
        ''' search path for executable '''
        return which(self.subst(val,attrs))

    def __cmd_current_user__(self,attrs):
        ''' return name of current user '''
        return current_user()

    def __cmd_abs_path__(self,attrs,val):
        ''' return abspath '''
        return abspath(self.subst(val,attrs))
    
    def __cmd_basename__(self,attrs,val):
        ''' return abspath '''
        return basename(self.subst(val,attrs))

    def __cmd_rand__(self,attrs,val):
        ''' rand string of length val'''
        count=int(val)
        choices=lowercase+digits 
        return ''.join(random.choice(choices) for x in range(count))

