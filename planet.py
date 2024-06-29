import pygame

class Planet:
    def __init__(self, pos, vel, acc, color, radius):
        self.pos = pos
        self.vel = vel
        self.acc = acc
        self.color = color
        self.radius = radius
    
    def to_dict(self):
        return {
            'pos': self.pos,
            'vel': self.vel,
            'acc': self.acc,
            'color': self.color,
            'radius': self.radius
        }

    @classmethod
    def from_dict(cls, dict_data):
        return cls(dict_data['pos'], dict_data['vel'], dict_data['acc'], dict_data['color'], dict_data['radius'])

    def __repr__(self):
        return f"Planet pos={self.pos}, vel={self.vel}, acc={self.acc}, color={self.color}, radius={self.radius}"