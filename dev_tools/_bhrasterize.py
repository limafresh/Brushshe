from multiprocessing import Process, SimpleQueue, cpu_count
from time import sleep


class BHRasterize:
    def __init__(self):
        self.num_workers = cpu_count()
        self.queue = SimpleQueue()
        self.workers = []
        self.manager = None
        self.queueResult = SimpleQueue()
        self.worker_result = None

        self.init()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exit()

    def producer(self, value):
        print("Producer: Running", flush=True)
        self.queue.put(value)

    def consumer(self, queue):
        # print('Debug: Consumer start')
        while True:
            item = queue.get()
            print("Debug: Consumer get data")

            if item is None:
                return

            if not hasattr(item, "type"):
                print(__name__, "wrong type")
                continue

            if item.type == 1:
                self.render_mask(item)

    def init(self):
        # class CustomManager(BaseManager):
        #     pass
        # CustomManager.register('BHRasterizeTask', BHRasterizeTask)
        # self.manager = CustomManager()
        # self.manager.start()

        self.workers = [Process(target=self.consumer, args=(self.queue,)) for _ in range(self.num_workers)]
        for worker in self.workers:
            worker.start()

        # producer_process = Process(target=self.producer, args=(1,))
        # producer_process.start()
        # producer_process.join()

    def exit(self):
        for _ in range(self.num_workers):
            self.queue.put(None)
        for worker in self.workers:
            worker.join()

    def render_mask(self, item):
        # output_data = item.output_image_data

        item.output_image_data = [111]


class BHRasterizeTask:
    def __init__(self, type: int, input_image_data, output_image_data):
        self.type = type
        self.input_image_data = input_image_data
        self.output_image_data = output_image_data


test = BHRasterize()
tasks = []
# TODO: https://zetcode.com/articles/tkinterlongruntask/

for _ in range(10):
    test.producer(tasks.append(BHRasterizeTask(1, [], [])))

sleep(2)
for task in tasks:
    print(task.output_image_data)

test.exit()
