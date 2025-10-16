# |---------------------------------------------------------------|
# |                                                               |
# |                  Give Feedback / Get Help                     |
# |    https://github.com/Saptha-me/sapthame/issues/new/choose    |
# |                                                               |
# |---------------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""This is the Sapthame.

Sapthame is the layer that makes swarms of agents.

In this swarm, each Bindu is a dot - annotating agents with the shared language of A2A, AP2, and X402.

Agents can be hosted anywhere — on laptops, clouds, or clusters — yet speak the same protocol, trust each other by design, and work together as a single, distributed mind.
A Goal Without a Plan Is Just a Wish. So Sapthame takes care Research, Plan and Implement.

Sapthame gives them the seven layers of connection — mind, memory, trust, task, identity, value, and flow — that’s why it’s called Sapthame. (Saptha, meaning “seven”; me, the self-aware network.)

"""

from .conductor import Conductor
from .state import State

__all__ = [
    "Conductor",
    "State",
]
