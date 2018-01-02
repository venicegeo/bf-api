package org.venice.beachfront.bfapi.database;

import java.io.Closeable;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.Collections;
import java.util.HashSet;
import java.util.Queue;
import java.util.Set;
import java.util.concurrent.ConcurrentLinkedQueue;

import javax.sql.DataSource;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class ConnectionManager {
	private final DataSource dataSource;
	private final Set<Connection> allConnections;
	private final Queue<Connection> availableConnections;
	private final int poolSize;
	
	public ConnectionManager(@Autowired DataSource dataSource, @Value("${DATABASE_POOL:#{10}}") int poolSize) {
		this.dataSource = dataSource;
		this.poolSize = poolSize;
		this.allConnections = Collections.synchronizedSet(new HashSet<>());
		this.availableConnections = new ConcurrentLinkedQueue<>();
		this.fillConnectionPool();
	}
	
	@SuppressWarnings("resource")
	private void fillConnectionPool() {
		
		int createConnections = this.poolSize - this.allConnections.size();
		for (int i=0; i<createConnections; i++) {
			Connection conn;
			try {
				conn = this.dataSource.getConnection();
			} catch (SQLException e) {
				e.printStackTrace();
				continue;
			}
			this.allConnections.add(conn);
			this.availableConnections.add(conn);
		}
	}
	
	@SuppressWarnings("resource")
	public PooledConnection getPooledConnection() throws SQLException {
		Connection conn = null;
		while (conn == null) {
			conn = this.availableConnections.remove();
			if (!conn.isValid(1)) {
				this.allConnections.remove(conn);
				conn = null;
				continue;
			}
		}
		return new PooledConnection(conn, this);
	}
	
	private void connectionDone(Connection conn) {
		this.availableConnections.add(conn);
	}
	
	public static class PooledConnection implements Closeable{
		private final Connection connection;
		private final ConnectionManager connectionManager;
		public PooledConnection(Connection connection, ConnectionManager connectionManager) {
			this.connection = connection;
			this.connectionManager = connectionManager;
		}
		
		public Connection getConnection() {
			return connection;
		}
		
		@Override
		public void close()  {
			this.connectionManager.connectionDone(this.connection);
		}
		
	}
	
	
}
