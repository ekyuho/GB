class MyTimer:
    def __init__(self):
        #timer={aename:{"data":-1, "state":-1,"file":-1}}  # -1 means inactive
        self.timer={}
        #self.expired={aename:{"data":False, "state":False,"file":False}}
        self.expired={}
        #self.max={aename:{"data":False, "state":False,"file":False}}
        self.max={}
    def set(self, aename, domain, sec):
        if not aename in self.timer: 
            self.timer[aename]={"data":-1, "state":-1,"file":-1}
            self.expired[aename]={"data":-1, "state":-1,"file":-1}
            self.max[aename]={"data":-1, "state":-1,"file":-1}
        if domain in {'state', 'file'}: self.timer[aename][domain] = sec*60
        else: self.timer[aename][domain] = sec
        self.expired[aename][domain] = False
        self.max[aename][domain] = sec
        self.current()
    
    def current(self):
        for x in self.timer:
            print(f'{x} {self.timer[x]} {self.max[x]} {self.expired[x]}')
    def update(self):
        for x in self.timer:
            if self.timer[x]['data'] == 0: 
                self.expired[x]['data'] = True
                self.timer[x]['data'] = self.max[x]['data']
            else:
                self.timer[x]['data'] -=1

            if self.timer[x]['state'] == 0: 
                self.expired[x]['state'] = True
                self.timer[x]['state'] = self.max[x]['state']
            else:
                self.timer[x]['state'] -=1

            if self.timer[x]['file'] == 0: 
                self.expired[x]['file'] = True
                self.timer[x]['file'] = self.max[x]['file']
            else:
                self.timer[x]['file'] -=1
        
    def ring(self, aename, domain):
        x= self.expired[aename][domain]
        self.expired[aename][domain] = False
        if x: print(f'timer ring {aename}/{domain}')
        return x
if __name__ == '__main__':
    a = MyTimer('abc')
    a.set('abc','data', 5)
    print(a.current('abc'))
