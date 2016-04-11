from __future__ import absolute_import, division, print_function

import atexit
import sys

from mesos.interface import mesos_pb2
from mesos.native import MesosSchedulerDriver

from . import log as logging
from .proxies import SchedulerProxy
from .proxies.messages import FrameworkInfo, encode


class Scheduler(object):

    # TODO envargs
    def __init__(self, name, user='', master='zk://localhost:2181/mesos',
                 *args, **kwargs):
        self.framework = FrameworkInfo(name=name, user=user, **kwargs)
        self.master = master

    def __call__(self):
        return self.run()

    def run(self):
        # TODO logging
        # TODO implicit aknoladgements

        driver = MesosSchedulerDriver(SchedulerProxy(self),
                                      encode(self.framework),
                                      self.master)
        atexit.register(driver.stop)

        # run things
        status = 0 if driver.run() == mesos_pb2.DRIVER_STOPPED else 1
        driver.stop()  # Ensure that the driver process terminates.
        sys.exit(status)

    def on_registered(self, driver, framework_id, master):
        """Event handler triggered when the scheduler successfully registers
           with a master.

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        framework_id : string
            Unique ID generated by the master
        master : Master
            Information about the master itself
        Returns
        -------
        self
        """
        pass

    def on_reregistered(self, driver, framework_id, master):
        """Event handler triggered when the scheduler re-registers with a newly
           elected master.

        This is only called when the scheduler has previously been registered.
        masterInfo contains information about the newly elected master.

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        framework_id : string
            Unique ID generated by the master
        master : Master
            Information about the master itself
        """
        pass

    def on_disconnected(self, driver):
        """Event handler triggereg when the scheduler becomes disconnected from
           the master.

        (e.g. the master fails and another is taking over)

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        """
        pass

    def on_offers(self, driver, offers):
        """Event handler triggered when resources have been offered to this
           framework.

        A single offer will only contain resources from a single slave.
        Resources associated with an offer will not be re-offered to _this_
        framework until either (a) this framework has rejected those resources
        (see SchedulerDriver.launchTasks) or (b) those resources have been
        rescinded (see Scheduler.on_rescinded).

        Note that resources may be concurrently offered to more than one
        framework at a time (depending on the allocator being used).  In that
        case, the first framework to launch tasks using those resources will be
        able to use them while the other frameworks will have those resources
        rescinded (or if a framework has already launched tasks with those
        resources then those tasks will fail with a TASK_LOST status and a
        message saying as much).

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        offers: list of Offer
            Resource offer instances
        """
        for offer in offers:
            logging.info('Offer {} declined'.format(offer.id))
            driver.decline(offer.id)

    def on_rescinded(driver, offer_id):
        """Event handler triggered when an offer is no longer valid.

        (e.g., the slave was lost or another framework used resources in the
        offer)

        If for whatever reason an offer is never rescinded (e.g., dropped
        message, failing over framework, etc.), a framework that attempts to
        launch tasks using an invalid offer will receive TASK_LOST status
        updates for those tasks (see Scheduler.on_offers).

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        offer_id: string
            The unique identifier of the Mesos offer
        """
        pass

    def on_update(self, driver, status):
        """Event handler triggered when the status of a task has changed.

        (e.g., a slave is lost and so the task is lost, a task finishes and an
        executor sends a status update saying so, etc.)

        If implicit acknowledgements are being used, then returning from this
        callback _acknowledges_ receipt of this status update!

        If for  whatever reason the scheduler aborts during this callback (or
        the process exits) another status update will be delivered (note,
        however, that this is currently not true if the slave sending the status
        update is lost/fails during that time).

        If explicit acknowledgements are in use, the scheduler must acknowledge
        this status on the driver.

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        offer_id: string
            The unique identifier of the Mesos offer
        """
        pass

    def on_message(self, driver, executor_id, slave_id, message):
        """Event handler triggered when an executor sends a message.

        These messages are best effort; do not expect a framework message to be
        retransmitted in any reliable fashion.

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        executor_id: string
            The unique identifier of the Mesos executor the message came from
        slave_id: string
            The unique identifier of the Mesos slave the message came from
        message: string
            Arbitrary byte stream
        """
        pass

    def on_slave_lost(self, driver, slave_id):
        """Event handler triggered when a slave has been determined unreachable.

        (e.g., machine failure, network partition.)

        Most frameworks will need to reschedule any tasks launched on this slave
        on a new slave.

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        slave_id: string
            The unique identifier of the lost Mesos slave
        """
        pass

    def on_executor_lost(self, driver, executor_id, slave_id, status):
        """Event handler triggered when an executor has exited/terminated.

        Note that any tasks running will have TASK_LOST status updates
        automatically generated.

        NOTE: This callback is not reliably delivered.

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        executor_id: string
            The unique identifier of the lost Mesos executor
        slave_id: string
            The unique identifier of the Mesos slave where the executor loss
            happened
        status: int
            TODO: figure it out
        """
        pass

    def on_error(self, driver, message):
        """Event handler triggered when there is an unrecoverable error in the
           scheduler or scheduler driver.

        The driver will be aborted BEFORE invoking this callback.

        Parameters
        ----------
        driver: SchedulerDriver
            Interface for interacting with Mesos Master
        message: string
            Arbitrary byte stream
        """
        pass


if __name__ == '__main__':
    from .utils import run_daemon

    scheduler = Scheduler(name='Base')
    run_daemon('Scheduler Process', scheduler)
