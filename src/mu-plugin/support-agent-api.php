<?php
/**
 * Plugin Name: Support Agent API
 * Description: Read-only diagnostic endpoints for the AI support agent.
 * Version: 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_action(
	'rest_api_init',
	function () {
		$permission = function () {
			return current_user_can( 'manage_options' );
		};

		register_rest_route(
			'support-agent/v1',
			'/env',
			array(
				'methods'             => 'GET',
				'callback'            => 'support_agent_get_env',
				'permission_callback' => $permission,
			)
		);

		register_rest_route(
			'support-agent/v1',
			'/error-log',
			array(
				'methods'             => 'GET',
				'callback'            => 'support_agent_get_error_log',
				'permission_callback' => $permission,
			)
		);
		register_rest_route(
			'support-agent/v1',
			'/plugins',
			array(
				'methods'             => 'GET',
				'callback'            => 'support_agent_get_plugins',
				'permission_callback' => $permission,
			)
		);
	}
);

/**
 * Collect environment information about the site.
 */
function support_agent_get_env() {
	global $wp_version, $wpdb;

	$theme = wp_get_theme();

	return array(
		'wp_version'          => $wp_version,
		'php_version'         => PHP_VERSION,
		'mysql_version'       => $wpdb->db_version(),
		'site_url'            => get_site_url(),
		'active_theme'        => $theme->get( 'Name' ),
		'theme_version'       => $theme->get( 'Version' ),
		'is_child_theme'      => (bool) $theme->parent(),
		'wp_debug'            => defined( 'WP_DEBUG' ) && WP_DEBUG,
		'wp_debug_log'        => defined( 'WP_DEBUG_LOG' ) && WP_DEBUG_LOG,
		'memory_limit'        => ini_get( 'memory_limit' ),
		'max_execution_time'  => ini_get( 'max_execution_time' ),
		'upload_max_filesize' => ini_get( 'upload_max_filesize' ),
		'multisite'           => is_multisite(),
	);
}

/**
 * Return the tail of the WordPress debug log.
 */
function support_agent_get_error_log( $request ) {
	$lines = absint( $request->get_param( 'lines' ) );
	$lines = $lines > 0 ? min( $lines, 200 ) : 50;

	$path = WP_CONTENT_DIR . '/debug.log';

	if ( ! file_exists( $path ) ) {
		return array(
			'exists'  => false,
			'path'    => $path,
			'message' => 'Debug log not found. Enable WP_DEBUG_LOG in wp-config.php.',
		);
	}

	$content = file( $path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES );
	$tail    = array_slice( $content, -$lines );

	return array(
		'exists'        => true,
		'path'          => $path,
		'total_lines'   => count( $content ),
		'returned_lines' => count( $tail ),
		'entries'       => $tail,
	);
}
/**
 * Return installed plugins with their status and version.
 */
function support_agent_get_plugins() {
	if ( ! function_exists( 'get_plugins' ) ) {
		require_once ABSPATH . 'wp-admin/includes/plugin.php';
	}

	$all     = get_plugins();
	$plugins = array();

	foreach ( $all as $file => $data ) {
		$plugins[] = array(
			'name'    => $data['Name'],
			'version' => $data['Version'],
			'active'  => is_plugin_active( $file ),
			'file'    => $file,
		);
	}

	usort(
		$plugins,
		function ( $a, $b ) {
			return $b['active'] <=> $a['active'];
		}
	);

	return array(
		'total'  => count( $plugins ),
		'active' => count( array_filter( $plugins, fn( $p ) => $p['active'] ) ),
		'plugins' => $plugins,
	);
}