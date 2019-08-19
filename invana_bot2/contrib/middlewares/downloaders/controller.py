from scrapy.exceptions import CloseSpider, IgnoreRequest


class IgnoreTraversalRequestsController(object):
    """
    This middleware will stop the requests when the scraper reaches the maximum traversal
    requests.

    TODO - currently max pages is considered as maximum requests, without considering
    retry requests.

    """

    def process_request(self, request, spider):
        current_request_traversal_id = request.meta.get("current_request_traversal_id")
        current_traversal_max_count = request.meta.get("current_traversal_max_count")
        if current_request_traversal_id != "init":
            current_request_traversal_count = spider.crawler.stats.get_value(
                'invana-stats/traversals/{}/requests_count'.format(current_request_traversal_id), spider=spider)
            if current_request_traversal_count > current_traversal_max_count:
                raise IgnoreRequest(
                    reason="max traversals for traversal_id: {} achieved".format(current_request_traversal_id))


class StopCrawlerController(object):
    """
        This middleware will stop the requests when the scraper reaches the maximum traversal
    requests.
    """

    def process_request(self, request, spider):
        spider_id = spider.spider_config.get("spider_id")
        spider_requests_count = spider.crawler.stats.get_value(
            'invana-stats/spiders/{}/requests_count'.format(spider_id),
            spider=spider)
