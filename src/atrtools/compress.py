"Simple compression routine."

class RepeatedValues:
    "Type for single value repeated."

    def __init__(self, value, repeats):
        self.value = value
        self.repeats = repeats

    def __repr__(self):
        return '{}(value={},repeats={})'.format(self.__class__.__name__, self.value, self.repeats)

    def export(self, table):
        "Export compressed values to buffer table"
        cmd = 128 if not self.value else 64

        for _ in range(0, self.repeats//cmd):
            table.append(0b00000000 if not self.value else 0b10000000) # 64 or 128 repeats
            if self.value: 
                table.append(self.value)

        rst = self.repeats%cmd
        if rst:
            table.append(0b00000000|rst if not self.value else 0b10000000|rst) # 64 or 128 repeats
            if self.value:
                table.append(self.value)

    def adjust_last(self, value):
        "Cannot adjust"
        return False

class UniqueValues:
    "Type for set of unique values."

    def __init__(self, values):
        self.values = values

    def __repr__(self):
        return '{}(values={})'.format(self.__class__.__name__, self.values)

    def export(self, table):
        "Export compressed values to buffer table"
        idx = 0
        for _ in range(0, len(self.values)//64):
            table.append(0b11000000) # 64 repeats
            table.extend(self.values[idx:idx+64])
            idx += 64
        rst = len(self.values)%64
        if rst:
            table.append(0b11000000 | rst)
            table.extend(self.values[idx:])
           
    def adjust_last(self, value):
        "Append value to values"
        self.values.append(value)
        return True

class Compress:
    "Compress class"

    def __init__(self, data):
        "Construct object from byte data."
        self.data = data
        self.len = len(data)
        self.__compressed = []
        self.__packed = []

    @property
    def compressed(self):
        return self.__compressed

    @property
    def packed(self):
        return self.__packed

    def compress(self):
        "Compress data"
        idx = 0
        while idx < self.len-1:
            cnt = 0
            while idx < self.len-1 and self.data[idx] == self.data[idx+1]:
                cnt += 1
                idx += 1
            if cnt:
                self.compressed.append(RepeatedValues(self.data[idx], cnt+1))
                idx += 1 
            else:
                buf = []
                while idx < self.len-1 and self.data[idx] != self.data[idx+1]:
                    buf.append(self.data[idx])
                    idx += 1
                if buf:
                    self.compressed.append(UniqueValues(buf))
        
        if idx != self.len:
            lst = self.data[-1]
            if self.compressed:
                if not self.compressed[-1].adjust_last(lst):
                    self.compressed.append(UniqueValues([lst]))
            else:
                self.compressed.append(UniqueValues([lst]))

    def pack(self):
        "Pack data to Atari format"
        for data in self.compressed:
            data.export(self.packed)
