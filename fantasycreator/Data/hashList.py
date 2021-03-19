"""
Python implementation of a HashList - O(n) add/search/delete
"""

# Built-in module
import uuid

class HashList: 
  
    # Constructor (creates a list and a hash) 
    def __init__(self): 
        self.arr = [] 
        self.hashd = {}  
  
    def add(self, *x): 
        for i in x:
            s = len(self.arr) 
            self.arr.append(i) 
            if i in self.hashd: 
                self.hashd[i].append(s)

            else:
                self.hashd[i] = [s]
  
    # Removes all occurences of x
    def remove(self, x): 
        index = self.hashd.get(x, None) 
        if index == None: 
            return
        
        if isinstance(x, uuid.UUID) or len(index) == 1:
            del self.hashd[x] 
            for i in sorted(index, reverse=True):
                size = len(self.arr) 
                last = self.arr[size - 1] 
                (self.arr[i], self.arr[size - 1]) = (self.arr[size - 1], 
                                    self.arr[i])
        
                del self.arr[-1] 
                self.hashd[last] = [i]
        else:
            for i in sorted(index, reverse=True):
                if x is self.arr[i]:
                    
                    size = len(self.arr) 
                    last = self.arr[size - 1] 
                    (self.arr[i], self.arr[size - 1]) = (self.arr[size - 1], 
                                        self.arr[i])
            
                    del self.arr[-1] 
                    # print([str(x) for x in self.hashd[last]])
                    self.hashd[last][self.hashd[last].index(size-1)] = i
                    self.hashd[x].remove(i)
                    break

        
        # print(f'Array: {[str(x) for x in self.arr]}')
        # print(f'Hash: {[str(x) for x in self.hashd]}')

  
    def search(self, x): 
        ret = None
        try:
            i = self.hashd[x]
            ret = [self.arr[i[k]] for k in range(len(i))]

        except Exception:
            pass
        return ret
    
    def clear(self):
        self.arr.clear()
        self.hashd.clear()
    
    def __len__(self):
        return len(self.arr)

    def __iter__(self):
        yield from self.arr
    
    def __contains__(self, x):
        if isinstance(x, uuid.UUID):
            return x in self.arr
        return any(x is char for char in self.arr)
        
    def __str__(self):
        return self.arr