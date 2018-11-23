import logging
from decimal import Decimal, getcontext
from functools import reduce
from random import shuffle
from time import time
from typing import List
import numba as nb
from numba import jitclass, int8, int64, njit, prange, jit
import humanfriendly

@jitclass(spec = [('RETREAT', int8),
                  ('ATTACK', int8),
                  ('WAIT', int8)])
class CMD(object):
    def __init__(self):
        self.RETREAT = 0
        self.ATTACK = 1
        self.WAIT = 2


# @jitclass(spec = [('general_id', int64)])
class General(object):
    def __init__(self, general_id: int):
        # self.id = general_id
        pass

    def is_me(self, general_id: int) -> bool:
        return False
        # return self.get_id() == general_id

    def process_message(self, msg: int) -> int:
        # logging.debug("General id: {0} Received: {1} Returning: {2}".format(self.get_id, msg.name, msg.name))
        return msg


# @jitclass(spec = [('general_id', int64)])
class Traitor(object):
    def __init__(self, general_id: int):
        # self.id = general_id
        pass

    def is_me(self, general_id: int) -> bool:
        return False

    def process_message(self, msg: int) -> int:
        # For now, make the traitor always change the message.
        if msg == CMD().ATTACK:
            return_message: int = CMD().RETREAT
        elif msg == CMD().RETREAT:
            return_message: int = CMD().WAIT
        else:
            return_message: int = CMD().ATTACK

        # logging.debug("General id: {0} Received: {1} Returning: {2}".format(self._id, msg.name, return_message))
        return return_message


class Commander(object):
    def __init__(self, command: int64):
        self.command: int64 = command

    def get_consensus(self, num_generals: int64, num_traitors: int64) -> int:
        print("Setting up {0} generals".format(num_generals))
        generals = []
        for id in range(num_generals - num_traitors):
            generals.append(id)

        print("Setting up {0} traitors".format(num_traitors))
        for id in range((num_generals - num_traitors), num_generals):
            generals.append(id * -1)

        # Mix up the generals, so we don't know which ones are traitors.
        shuffle(generals)

        command = self.command
        return get_consensus_internal(generals, command)


@jit(nogil=True, cache = True)
def get_consensus_internal(generals: nb.types.List(int64, reflected = True), command: int) -> int:
    msgs = forward_messages(generals, command)
    consensus = get_majority_vote(msgs)
    # Get the index for that command, fetch it's string value.
    for k in range(3):
        if k == consensus:
            return k


@jit(nogil= True, parallel = True)
def forward_messages(generals: nb.types.List(int64), command: int):
    messages_from_lieutenants = []
    for index in prange(len(generals)):
        msg_from_lieutenant = send_message_to_generals(generals = generals,
                                                       general_id = generals[index],
                                                       depth = 1,
                                                       command = command)
        messages_from_lieutenants.append(msg_from_lieutenant)

    return messages_from_lieutenants


@njit(nogil=True, cache = True)
def my_max(lst: List[int64]):
    curr_max = lst[0]
    for i in lst:
        if i > curr_max:
            curr_max = i
    return curr_max


@njit(nogil=True, cache = True)
def get_majority_vote(votes: List[int64]):
    vote_agg = [int64(0)] * 3
    for v in votes:
        vote_agg[v] += int64(1)

    def get_max_vote():
        output = []
        for vote in vote_agg:
            if vote == my_max(vote_agg):
                output.append(vote)
        return output

    if len(get_max_vote()) > 1:
        # We have a tie
        return -1
    else:
        return vote_agg.index(my_max(vote_agg))


# @njit(nogil=True, cache = True)
def send_message_to_generals(generals: nb.types.List(int),
                             general_id: int,
                             depth: int,
                             command: int) -> int:
    msg_from_generals = []

    is_loyal = general_id > 0
    # print("General is loyal: {0} - {1}".format(is_loyal, depth))

    for index, other_general in enumerate(generals):
        # Don't ask yourself!
        if not abs(other_general) == abs(general_id):
            if depth > 0:
                # If we are not in the base case, ask every other general.
                msg_from_general = send_message_to_generals(generals = generals,
                                                            general_id = generals[index],
                                                            depth = depth - 1,
                                                            command = command
                                                                if is_loyal or abs(generals[index]) % 2 == 1
                                                                else (command + 1) % 2)
            else:
                # If we reach the base case, just ask directly.
                if other_general > 0:
                    msg_from_general = command
                else:
                    # This is a traitor, so change the message.
                    msg_from_general = command \
                                            if abs(other_general) % 2 == 1 \
                                            else (command + 1) % 2

            if msg_from_general > -1:
                msg_from_generals.append(msg_from_general)

                # Once we have consensus, return it.
                current_consensus = get_majority_vote(msg_from_generals)
                if current_consensus > -1 and len(msg_from_generals) > 2:
                    # print("Used {0} for consensus: ".format(len(msg_from_generals)))
                    return current_consensus

    return get_majority_vote(msg_from_generals)


def pi():
    getcontext().prec = 100_000_000

    outer = Decimal(1 / Decimal(2 ** 6))
    from multiprocessing.dummy import Pool
    from multiprocessing import cpu_count
    pool = Pool(processes = cpu_count() - 1)

    def sum(n=0):
        curr_list = list(pool.map(index, range(n+1)))
        # curr_list.append(index(0))
        return reduce(lambda x, y: x + y, curr_list, Decimal(0.0))

    def index(n=0):
        four_n = Decimal(4 * n)
        ten_n = Decimal(10 * n)

        num = Decimal((-1) ** n)
        den = Decimal(2 ** ten_n)

        rest = - Decimal(2 ** 5) / Decimal(four_n + 1) \
                       - Decimal(1 / Decimal(four_n + 3)) \
                       + Decimal(Decimal(2 ** 8) / Decimal(ten_n + 1)) \
                       - Decimal(Decimal(2 ** 6) / Decimal(ten_n + 3)) \
                       - Decimal(Decimal(2 ** 2) / Decimal(ten_n + 5)) \
                       - Decimal(Decimal(2 ** 2) / Decimal(ten_n + 7)) \
                       - Decimal(1 / Decimal(ten_n + 9))
        return Decimal(Decimal(num / den) * rest)

    print("Calculating Pi")
    print("10:            {:0.200}".format(outer * sum(n = 10)))
    print("100:           {:0.200}".format(outer * sum(n = 100)))
    print("1000:          {:0.200}".format(outer * sum(n = 1_000)))
    print("10,000:        {:0.200}".format(outer * sum(n = 10_000)))
    print("100,000:       {:0.200}".format(outer * sum(n = 100_000)))
    # print("1,000,000:     {:0.200}".format(outer * sum(n = 1_000_000)))
    # print("1,000,000,000: {:0.200}".format(outer * sum(n = 1_000_000_000)))
    print("Enjoy the Pi!")


if __name__ == "__main__":
    cmd_to_send = CMD().ATTACK

    NUM_GENERALS = 100_000
    TRAITOR_RATIO = 1.0/3.0

    commander = Commander(command=cmd_to_send)
    print("Starting sending.")

    pi()
    start = time()
    final_decision = commander.get_consensus(NUM_GENERALS, int(NUM_GENERALS * TRAITOR_RATIO))
    end = time()

    if cmd_to_send is final_decision:
        print("Achieved consensus in: {0}".format(humanfriendly.format_timespan(end - start)))
    else:
        print("Failed to achieve consensus while wasting: {0}".format(humanfriendly.format_timespan(end - start)))
        exit(1)
