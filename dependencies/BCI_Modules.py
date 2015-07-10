class FIFO:
    @staticmethod
    def Erase(File):
        newFile = open(File,'w+')
        newFile.write(" ")
        newFile.close()
        
    @staticmethod
    def Rewrite(File, Message):
        newFile = open(File,'w+')
        newFile.write(Message)
        newFile.close()

    @staticmethod
    def Check(File, Message):
        newFile = open(File,'r')
        if (newFile.readline() == Message):
            newFile.close()
            return True

    @staticmethod
    def Wait(File,Message):
        while True:
            newFile = open(File,'r')
            if (newFile.readline() == Message):
                newFile.close()
                break
            newFile.close()

    @staticmethod
    def Read(File):
        newFile = open(File,'r')
        Line = newFile.readline()
        newFile.close()
        return Line


class Synchronize(object):
    def __init__(self,Target):
        self.connection = Target

    def Wait(self,Message):
        while True:
            if (self.connection.recv(32) == Message):
                break

    def Check(self,Message1,Message2):
        Feed = self.connection.recv(32)
        if (Feed == Message1):
            return 1
        elif (Feed == Message2):
            return 2
        return 3
