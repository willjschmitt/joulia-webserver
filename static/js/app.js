define(['jquery','angularAMD','angular-route','angular-resource','angular-ui',
        "bemat-common",
    ],function($,angularAMD){
	var app = angular.module('joulia', ['ngRoute','ngResource','ui.bootstrap'])
		.config(['$locationProvider', '$routeProvider',function config($locationProvider, $routeProvider) {
			$locationProvider.hashPrefix('!');
			$routeProvider
				.when('/brewery/:breweryId', angularAMD.route({
					templateUrl:'static/brewery/html/brewery.html',
					controller:'breweryController',
					controllerUrl:'brewery'
				}))
				.when('/recipes/', angularAMD.route({
					templateUrl:'static/brewery/html/recipes.html',
					controller:'recipesController',
					controllerUrl:'recipes'
				}))
				.when('/recipe/:recipeId', angularAMD.route({
					templateUrl:'static/brewery/html/recipe.html',
					controller:'recipeController',
					controllerUrl:'recipe'
				}))
				.otherwise('/');
		}])
		.config(['$httpProvider', function($httpProvider){
	        // django and angular both support csrf tokens. This tells
	        // angular which cookie to add to what header.
	        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
	        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
	    }]);
	return angularAMD.bootstrap(app);
});