events=[[1,3],[2,4],[5,9],[6,8],[7,9]]
answer=[[1,4],[5,9]]
def mergeevents(a,b):
    
    if (a[1]>=b[0] and a[1] <= b[1]) or a[0]>=b[0] and a[0]<=b[1] or b[0]>=a[0] and b[0]<=a[1] or b[1]>=a[0] and b[1]<=a[1]:
        return [min(a[0],b[0]),max(a[1],b[1])],None
    else:
        return a,b


ans=[events[0]]
for i in range(1,len(events)):
    a,b=mergeevents(ans[-1],events[i])
    print(a,b)
    if b==None: 
        ans[-1]=a
    else: 
        ans.append(b)
print(ans)






