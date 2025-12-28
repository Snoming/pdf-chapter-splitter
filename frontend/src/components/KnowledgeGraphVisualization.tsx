// 知识图谱可视化组件
// 使用D3.js实现知识图谱的可视化展示，优化了小窗口显示效果

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import * as d3 from 'd3';

interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: any;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface KnowledgeGraphLink {
  source: string | KnowledgeGraphNode;
  target: string | KnowledgeGraphNode;
  relation: string;
  weight: number;
}

interface KnowledgeGraphVisualizationProps {
  graph: any;
  width?: number | string;
  height?: number | string;
  isBuilding?: boolean;
}

// 定义最小支持分辨率
const MIN_SUPPORTED_WIDTH = 320;
const MIN_SUPPORTED_HEIGHT = 400;

const KnowledgeGraphVisualization: React.FC<KnowledgeGraphVisualizationProps> = ({
  graph,
  width = 800,
  height = 600,
  isBuilding = false
}) => {
  // 使用useMemo优化数据转换，避免不必要的重复计算，并添加数据验证
  const data = useMemo(() => {
    const nodes = (graph?.nodes || []).map((node: any) => ({
      id: node.id,
      label: node.content || node.label || '未知节点',
      type: node.type,
      metadata: node.metadata
    }));
    
    const links = (graph?.edges || []).map((edge: any) => ({
      source: edge.source_id,
      target: edge.target_id,
      relation: edge.relation_type,
      weight: edge.weight
    }));
    
    // 数据验证：确保所有节点都有正确的父子关系
    const nodeIdSet = new Set<string>(nodes.map((node: KnowledgeGraphNode) => node.id));
    const parentNodeSet = new Set<string>(links.map((link: KnowledgeGraphLink) => link.source as string));
    
    // 检查每个节点是否有父节点（除了书籍节点）
    const orphanedNodes = nodes.filter((node: KnowledgeGraphNode) => {
      if (node.type === 'book') return false;
      return !parentNodeSet.has(node.id);
    });
    
    // 记录孤立节点（仅用于调试）
    if (orphanedNodes.length > 0) {
      console.warn('知识图谱中存在孤立节点：', orphanedNodes);
    }
    
    // 确保所有链接的源节点和目标节点都存在
    const validLinks = links.filter((link: KnowledgeGraphLink) => {
      const source = typeof link.source === 'string' ? link.source : link.source.id;
      const target = typeof link.target === 'string' ? link.target : link.target.id;
      const sourceExists = nodeIdSet.has(source);
      const targetExists = nodeIdSet.has(target);
      if (!sourceExists || !targetExists) {
        console.warn('知识图谱中存在无效链接：', link);
      }
      return sourceExists && targetExists;
    });
    
    return { 
      nodes, 
      links: validLinks,
      metadata: {
        orphanedNodes: orphanedNodes.length,
        validLinks: validLinks.length,
        totalNodes: nodes.length,
        totalLinks: links.length
      }
    };
  }, [graph]);
  
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<KnowledgeGraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<KnowledgeGraphNode | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [viewport, setViewport] = useState({
    width: typeof width === 'string' ? 800 : width,
    height: typeof height === 'string' ? 600 : height
  });
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const simulationRef = useRef<d3.Simulation<any, any> | null>(null);
  const prevViewportRef = useRef(viewport);

  // Toggle node expansion
  const toggleNodeExpansion = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  // Check if a node has children
  const hasChildren = useCallback((nodeId: string) => {
    return data.links.some((link: KnowledgeGraphLink) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      return sourceId === nodeId;
    });
  }, [data.links]);

  // Check if a node is expanded
  const isNodeExpanded = useCallback((nodeId: string) => {
    return expandedNodes.has(nodeId);
  }, [expandedNodes]);

  // Get all child nodes of a given node
  const getChildNodes = useCallback((nodeId: string) => {
    const childIds = new Set<string>();
    
    // Find direct children
    data.links.forEach((link: KnowledgeGraphLink) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      if (sourceId === nodeId) {
        const targetId = typeof link.target === 'string' ? link.target : link.target.id;
        if (targetId) {
          childIds.add(targetId);
        }
      }
    });
    
    return childIds;
  }, [data.links]);

  // Get all descendants of a given node (including indirect children)
  const getDescendants = useCallback((nodeId: string) => {
    const descendants = new Set<string>();
    const queue = [nodeId];
    
    while (queue.length > 0) {
      const currentId = queue.shift();
      if (currentId) {
        const children = getChildNodes(currentId);
        children.forEach(childId => {
          if (!descendants.has(childId)) {
            descendants.add(childId);
            queue.push(childId);
          }
        });
      }
    }
    
    return descendants;
  }, [getChildNodes]);

  // Filter nodes to show based on expanded state
  const visibleNodes = useMemo(() => {
    if (data.nodes.length === 0) return [];
    
    // Always show book and chapter nodes
    const visible = new Set<string>();
    const rootNodes = data.nodes.filter((node: KnowledgeGraphNode) => node.type === 'book');
    
    // Add root nodes
    rootNodes.forEach((node: KnowledgeGraphNode) => visible.add(node.id));
    
    // Add all chapter nodes
    data.nodes.forEach((node: KnowledgeGraphNode) => {
      if (node.type === 'chapter') {
        visible.add(node.id);
      }
    });
    
    // Add expanded nodes and their descendants
    expandedNodes.forEach((nodeId: string) => {
      const descendants = getDescendants(nodeId);
      descendants.forEach((descendantId: string) => visible.add(descendantId));
    });
    
    return data.nodes.filter((node: KnowledgeGraphNode) => visible.has(node.id));
  }, [data.nodes, expandedNodes, getDescendants]);

  // Filter links to show based on visible nodes
  const visibleLinks = useMemo(() => {
    if (data.links.length === 0) return [];
    
    const visibleNodeIds = new Set<string>(visibleNodes.map((node: KnowledgeGraphNode) => node.id));
    
    return data.links.filter((link: KnowledgeGraphLink) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target.id;
      return sourceId && targetId && visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId);
    });
  }, [data.links, visibleNodes]);

  // Memoized filtered data for visualization
  const filteredData = useMemo(() => {
    return {
      nodes: visibleNodes,
      links: visibleLinks
    };
  }, [visibleNodes, visibleLinks]);

  // 响应式处理 - 确保最小支持分辨率
  const handleResize = useCallback(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      // 确保视口不小于最小支持分辨率
      const newWidth = Math.max(clientWidth, MIN_SUPPORTED_WIDTH);
      const newHeight = Math.max(clientHeight - 20, MIN_SUPPORTED_HEIGHT);
      
      // 只有当视口大小变化超过5%时才更新，避免频繁重绘
      const widthChange = Math.abs(newWidth - viewport.width) / viewport.width;
      const heightChange = Math.abs(newHeight - viewport.height) / viewport.height;
      
      if (widthChange > 0.05 || heightChange > 0.05) {
        setIsAnimating(true);
        setViewport(prev => {
          prevViewportRef.current = prev;
          return { width: newWidth, height: newHeight };
        });
      }
    }
  }, [viewport]);

  useEffect(() => {
    // 初始化视口大小
    handleResize();
    
    // 监听窗口大小变化
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize]);
  
  // 当视口变化时，添加平滑过渡效果
  useEffect(() => {
    if (isAnimating) {
      const timer = setTimeout(() => setIsAnimating(false), 500);
      return () => clearTimeout(timer);
    }
  }, [isAnimating]);

  useEffect(() => {
    if (!svgRef.current || !filteredData || !filteredData.nodes || !filteredData.links) return;

    const svg = d3.select(svgRef.current);
    
    // 使用平滑过渡更新SVG尺寸
    svg.transition().duration(300)
       .attr('width', viewport.width)
       .attr('height', viewport.height);

    // 定义颜色比例尺
    const nodeColors = d3.scaleOrdinal<string, string>()
      .domain(['book', 'chapter', 'section', 'knowledge'])
      .range(['#2c3e50', '#3498db', '#27ae60', '#e74c3c']);
    
    // 定义关系类型颜色比例尺
    const edgeColors = d3.scaleOrdinal<string, string>()
      .domain(['contains', 'related_to', 'depends_on', 'similar_to', 'extends', 'instance_of'])
      .range(['#95a5a6', '#3498db', '#e74c3c', '#f39c12', '#27ae60', '#9b59b6']);

    // 辅助函数：判断是否为小视口
    const isSmallViewport = () => {
      return viewport.width < 600 || viewport.height < 400;
    };

    // 优化的节点半径计算函数
    const getNodeRadius = (d: any, viewportWidth: number) => {
      const baseRadiusMap: Record<string, number> = {
        'book': viewportWidth < 600 ? 20 : 25,
        'chapter': viewportWidth < 600 ? 16 : 18,
        'section': viewportWidth < 600 ? 12 : 14,
        'knowledge': viewportWidth < 600 ? 8 : 10
      };
      
      const baseRadius = baseRadiusMap[d.type] || (viewportWidth < 600 ? 9 : 12);
      // 根据标签长度和视口大小微调半径
      const labelLength = d.label.length;
      const radiusAdjustment = Math.min(labelLength * 0.25, viewportWidth < 600 ? 3 : 5);
      
      return baseRadius + radiusAdjustment;
    };
    
    // 优化的字体大小计算函数
    const getNodeFontSize = (d: any, viewportWidth: number) => {
      const fontSizeMap: Record<string, number> = {
        'book': viewportWidth < 600 ? 10 : 13,
        'chapter': viewportWidth < 600 ? 9 : 11,
        'section': viewportWidth < 600 ? 8 : 10,
        'knowledge': viewportWidth < 600 ? 7 : 9
      };
      
      return fontSizeMap[d.type] || (viewportWidth < 600 ? 8 : 10);
    };
    
    // 优化的标签截断函数
    const truncateLabel = (label: string, type: string, viewportWidth: number) => {
      let maxLength;
      if (viewportWidth < 400) {
        maxLength = type === 'knowledge' ? 6 : type === 'section' ? 8 : 10;
      } else if (viewportWidth < 600) {
        maxLength = type === 'knowledge' ? 8 : type === 'section' ? 10 : 12;
      } else if (viewportWidth < 800) {
        maxLength = type === 'knowledge' ? 12 : type === 'section' ? 15 : 18;
      } else {
        maxLength = type === 'knowledge' ? 16 : type === 'section' ? 20 : 24;
      }
      
      return label.length > maxLength ? label.substring(0, maxLength) + '...' : label;
    };

    // 根据视口大小动态调整力导向参数
    const getForceParameters = () => {
      const isVerySmallViewport = viewport.width < 400 || viewport.height < 300;
      
      return {
        // 电荷强度，小窗口下更强的排斥力避免节点重叠
        chargeStrength: isVerySmallViewport ? -1200 : isSmallViewport() ? -800 : -500,
        // 链接距离，小窗口下更短的距离
        linkDistance: isVerySmallViewport ? 40 : isSmallViewport() ? 60 : 100,
        // 碰撞半径系数，小窗口下稍大的碰撞半径确保可点击性
        collisionRadiusFactor: isVerySmallViewport ? 1.2 : isSmallViewport() ? 1.0 : 0.9,
        // 重力强度，小窗口下更强的重力将节点聚集
        gravity: isVerySmallViewport ? 0.08 : isSmallViewport() ? 0.05 : 0.02,
        // 中心力强度
        centerStrength: isVerySmallViewport ? 0.8 : isSmallViewport() ? 0.5 : 0.3
      };
    };

    const forceParams = getForceParameters();
    
    // 创建或选择容器组
    let g = svg.select<SVGGElement>('g');
    if (g.empty()) {
      g = svg.append<SVGGElement>('g');
    }

    // 创建或更新缩放行为
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.05, 15])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        
        // 根据缩放级别动态调整标签显示
        const scale = event.transform.k;
        g.selectAll('.node text')
          .style('visibility', () => scale < 0.5 ? 'hidden' : 'visible')
          .style('font-size', (d: any) => {
            const baseSize = getNodeFontSize(d, viewport.width);
            return `${Math.max(baseSize * scale, 4)}px`;
          });
      });

    // 应用缩放
    svg.call(zoom);

    // 保存当前节点位置，用于平滑过渡
    const currentPositions = new Map<string, { x: number; y: number }>(filteredData.nodes.map((node: any) => [node.id, {
      x: (node as any).x || viewport.width / 2,
      y: (node as any).y || viewport.height / 2
    }]));
    
    // 平滑过渡到新位置
    filteredData.nodes.forEach((node: any) => {
      const pos = currentPositions.get(node.id);
      if (pos) {
        (node as any).x = pos.x;
        (node as any).y = pos.y;
      }
    });

    // 创建或重启力导向模拟
    const simulation = d3.forceSimulation<KnowledgeGraphNode, KnowledgeGraphLink>(filteredData.nodes)
      .force('link', d3.forceLink<KnowledgeGraphNode, KnowledgeGraphLink>(filteredData.links)
        .id((d: any) => d.id)
        .distance((d: any) => {
          // 根据关系类型、权重和视口大小智能调整距离
          let baseDistance = forceParams.linkDistance;
          if (d.relation === 'contains') baseDistance *= 0.7;
          if (d.relation === 'depends_on') baseDistance *= 1.2;
          return baseDistance * (1 / Math.sqrt(d.weight));
        })
        .strength((d: any) => {
          // 父子关系更强的连接强度
          return d.relation === 'contains' ? 0.9 : 0.6;
        })
      )
      .force('charge', d3.forceManyBody()
        .strength(forceParams.chargeStrength)
        .distanceMin(20)
        .distanceMax(isSmallViewport() ? 150 : 250)
      )
      .force('center', d3.forceCenter(viewport.width / 2, viewport.height / 2)
        .strength(forceParams.centerStrength)
      )
      .force('collision', d3.forceCollide().radius((d: any) => {
        return getNodeRadius(d, viewport.width) * forceParams.collisionRadiusFactor;
      }))
      // 增强的重力，使节点更好地聚集在中心区域
      .force('gravity', d3.forceRadial(0, viewport.width / 2, viewport.height / 2)
        .strength(forceParams.gravity)
        .radius(viewport.width / 3)
      )
      .alphaDecay(0.015)
      .velocityDecay(0.35);

    simulationRef.current = simulation as any;

    // 绘制连线
    const link = g.selectAll<SVGLineElement, any>('line.link')
      .data(data.links, (d: any) => `${typeof d.source === 'string' ? d.source : d.source.id}-${typeof d.target === 'string' ? d.target : d.target.id}-${d.relation}`);
    
    // 进入选择 - 新添加的连线
    const linkEnter = link.enter().append<SVGLineElement>('line')
      .attr('class', 'link')
      .attr('stroke', (d: any) => edgeColors(d.relation) || '#999')
      .attr('stroke-opacity', 0)
      .attr('stroke-width', (d: any) => {
        const baseWidth = Math.sqrt(d.weight);
        return Math.max(baseWidth, isSmallViewport() ? 1.2 : 1.5);
      });
    
    // 更新选择 - 已存在的连线
    linkEnter.merge(link)
      .transition().duration(500)
      .attr('stroke', (d: any) => edgeColors(d.relation) || '#999')
      .attr('stroke-opacity', 0.8)
      .attr('stroke-width', (d: any) => {
        const baseWidth = Math.sqrt(d.weight);
        return Math.max(baseWidth, isSmallViewport() ? 1.2 : 1.5);
      });
    
    // 退出选择 - 移除的连线
    link.exit().remove();

    // 绘制节点组
    const node = g.selectAll<SVGGElement, any>('g.node')
      .data(filteredData.nodes, (d: KnowledgeGraphNode) => d.id);
    
    // 进入选择 - 新添加的节点
    const nodeEnter = node.enter().append<SVGGElement>('g')
      .attr('class', 'node')
      .call(d3.drag<any, any>()
        .on('start', function(event, d: any) {
          if (!event.active) simulation.alphaTarget(0.4).restart();
          d.fx = d.x;
          d.fy = d.y;
          
          // 高亮拖拽的节点
          d3.select(this).select('circle')
            .transition().duration(200)
            .attr('stroke', '#000')
            .attr('stroke-width', 3)
            .attr('r', () => getNodeRadius(d, viewport.width) * 1.2);
        })
        .on('drag', function(event, d: any) {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', function(event, d: any) {
          if (!event.active) simulation.alphaTarget(0);
          // 保留拖拽后的位置
          d.fx = null;
          d.fy = null;
          
          // 恢复节点样式
          d3.select(this).select('circle')
            .transition().duration(200)
            .attr('stroke', selectedNode?.id === d.id ? '#000' : '#fff')
            .attr('stroke-width', selectedNode?.id === d.id ? 3 : isSmallViewport() ? 1.2 : 2)
            .attr('r', () => getNodeRadius(d, viewport.width));
        }));
    
    // 添加节点圆圈
    nodeEnter.append<SVGCircleElement>('circle')
      .attr('r', 0)
      .attr('fill', (d: any) => nodeColors(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', isSmallViewport() ? 1.2 : 2)
      .style('cursor', 'pointer');
    
    // 添加展开/折叠指示器
    nodeEnter.append<SVGGElement>('g')
      .attr('class', 'expand-indicator')
      .style('cursor', 'pointer')
      .style('pointer-events', (d: any) => hasChildren(d.id) ? 'auto' : 'none')
      .append<SVGCircleElement>('circle')
      .attr('r', (d: any) => getNodeRadius(d, viewport.width) * 0.4)
      .attr('cx', (d: any) => getNodeRadius(d, viewport.width) + 5)
      .attr('cy', 0)
      .attr('fill', '#fff')
      .attr('stroke', '#333')
      .attr('stroke-width', 1.5);
    
    // 添加展开/折叠箭头
    nodeEnter.append<SVGPathElement>('path')
      .attr('class', 'expand-arrow')
      .attr('d', (d: any) => {
        const radius = getNodeRadius(d, viewport.width);
        if (isNodeExpanded(d.id)) {
          return `M${radius + 5},${-radius * 0.2} L${radius + 5},${radius * 0.2}`;
        } else {
          return `M${radius + 5 - radius * 0.2},0 L${radius + 5 + radius * 0.2},0`;
        }
      })
      .attr('fill', 'none')
      .attr('stroke', '#333')
      .attr('stroke-width', 1.5)
      .style('cursor', 'pointer')
      .style('pointer-events', (d: any) => hasChildren(d.id) ? 'auto' : 'none');
    
    // 添加节点标签
    nodeEnter.append<SVGTextElement>('text')
      .attr('dx', 0)
      .attr('dy', '.35em')
      .attr('text-anchor', 'middle')
      .attr('fill', '#333')
      .attr('pointer-events', 'none')
      .attr('user-select', 'none')
      .attr('stroke', isSmallViewport() ? '#fff' : 'none')
      .attr('stroke-width', isSmallViewport() ? 0.6 : 0)
      .attr('font-size', (d: any) => getNodeFontSize(d, viewport.width))
      .text((d: any) => truncateLabel(d.label, d.type, viewport.width));
    
    // 添加鼠标事件处理
    node.on('mouseover', (event, d: any) => {
      setHoveredNode(d);
      
      // 高亮相关节点和边
      g.selectAll<SVGCircleElement, any>('.node circle')
        .transition().duration(200)
        .attr('stroke', (nd: any) => nd.id === d.id ? '#000' : '#fff')
        .attr('stroke-width', (nd: any) => nd.id === d.id ? 3 : isSmallViewport() ? 1.2 : 2)
        .attr('r', (nd: any) => {
          const baseRadius = getNodeRadius(nd, viewport.width);
          return nd.id === d.id ? baseRadius * 1.2 : baseRadius;
        });
      
      g.selectAll<SVGLineElement, any>('.link')
        .transition().duration(200)
        .attr('stroke-opacity', (l: any) => {
          const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
          const targetId = typeof l.target === 'string' ? l.target : l.target.id;
          return (sourceId === d.id || targetId === d.id) ? 1.0 : 0.4;
        })
        .attr('stroke-width', (l: any) => {
          const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
          const targetId = typeof l.target === 'string' ? l.target : l.target.id;
          const baseWidth = Math.sqrt(l.weight);
          return (sourceId === d.id || targetId === d.id) ? Math.max(baseWidth * 1.8, isSmallViewport() ? 1.8 : 2.2) : baseWidth;
        });
    })
    .on('mouseout', () => {
      setHoveredNode(null);
      
      // 恢复默认样式
      g.selectAll<SVGCircleElement, any>('.node circle')
        .transition().duration(200)
        .attr('stroke', '#fff')
        .attr('stroke-width', isSmallViewport() ? 1.2 : 2)
        .attr('r', (d: any) => getNodeRadius(d, viewport.width));
      
      g.selectAll<SVGLineElement, any>('.link')
        .transition().duration(200)
        .attr('stroke-opacity', 0.8)
        .attr('stroke-width', (d: any) => {
          const baseWidth = Math.sqrt(d.weight);
          return Math.max(baseWidth, isSmallViewport() ? 1.2 : 1.5);
        });
    })
    .on('click', (event, d: any) => {
      event.stopPropagation();
      
      // 检查是否点击了展开/折叠指示器
      const target = event.target as SVGElement;
      if (target.closest('.expand-indicator') || target.classList.contains('expand-arrow')) {
        // 切换节点展开状态
        toggleNodeExpansion(d.id);
      } else {
        // 选中节点
        setSelectedNode(d);
        
        // 高亮选中节点和相关连接
        g.selectAll<SVGCircleElement, any>('.node circle')
          .transition().duration(200)
          .attr('stroke', (nd: any) => nd.id === d.id ? '#000' : '#fff')
          .attr('stroke-width', (nd: any) => nd.id === d.id ? 3 : isSmallViewport() ? 1.2 : 2);
        
        g.selectAll<SVGLineElement, any>('.link')
          .transition().duration(200)
          .attr('stroke', (l: any) => {
            const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
            const targetId = typeof l.target === 'string' ? l.target : l.target.id;
            return (sourceId === d.id || targetId === d.id) ? '#000' : edgeColors(l.relation) || '#999';
          })
          .attr('stroke-width', (l: any) => {
            const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
            const targetId = typeof l.target === 'string' ? l.target : l.target.id;
            const baseWidth = Math.sqrt(l.weight);
            return (sourceId === d.id || targetId === d.id) ? Math.max(baseWidth * 1.8, isSmallViewport() ? 1.8 : 2.2) : baseWidth;
          });
      }
    });
    
    // 更新节点组
    node.select<SVGCircleElement>('circle')
      .transition().duration(400)
      .attr('r', (d: any) => getNodeRadius(d, viewport.width))
      .attr('fill', (d: any) => nodeColors(d.type))
      .attr('stroke-width', isSmallViewport() ? 1.2 : 2);
    
    // 更新展开/折叠指示器
    node.select('.expand-indicator circle')
      .attr('cx', (d: any) => getNodeRadius(d, viewport.width) + 5)
      .attr('r', (d: any) => getNodeRadius(d, viewport.width) * 0.4)
      .style('pointer-events', (d: any) => hasChildren(d.id) ? 'auto' : 'none')
      .style('opacity', (d: any) => hasChildren(d.id) ? 1 : 0);
    
    // 更新展开/折叠箭头
    node.select('.expand-arrow')
      .transition().duration(200)
      .attr('d', (d: any) => {
        const radius = getNodeRadius(d, viewport.width);
        if (isNodeExpanded(d.id)) {
          return `M${radius + 5},${-radius * 0.2} L${radius + 5},${radius * 0.2}`;
        } else {
          return `M${radius + 5 - radius * 0.2},0 L${radius + 5 + radius * 0.2},0`;
        }
      })
      .style('pointer-events', (d: any) => hasChildren(d.id) ? 'auto' : 'none')
      .style('opacity', (d: any) => hasChildren(d.id) ? 1 : 0);
    
    // 更新节点标签
    node.select<SVGTextElement>('text')
      .transition().duration(400)
      .text((d: any) => truncateLabel(d.label, d.type, viewport.width))
      .attr('font-size', (d: any) => getNodeFontSize(d, viewport.width))
      .attr('stroke', isSmallViewport() ? '#fff' : 'none')
      .attr('stroke-width', isSmallViewport() ? 0.6 : 0);
    
    // 退出选择 - 移除的节点
    node.exit().remove();

    // 添加背景点击事件，取消选中
    svg.on('click', () => {
      setSelectedNode(null);
      
      // 恢复默认样式
      g.selectAll<SVGCircleElement, any>('.node circle')
        .transition().duration(200)
        .attr('stroke', '#fff')
        .attr('stroke-width', isSmallViewport() ? 1.2 : 2);
      
      g.selectAll<SVGLineElement, any>('.link')
        .transition().duration(200)
        .attr('stroke', (d: any) => edgeColors(d.relation) || '#999')
        .attr('stroke-width', (d: any) => {
          const baseWidth = Math.sqrt(d.weight);
          return Math.max(baseWidth, isSmallViewport() ? 1.2 : 1.5);
        });
    });

    simulation.alpha(0.3).restart();

    // 更新位置
    simulation.on('tick', () => {
      g.selectAll<SVGLineElement, any>('.link')
        .attr('x1', (d: any) => (d.source as any).x)
        .attr('y1', (d: any) => (d.source as any).y)
        .attr('x2', (d: any) => (d.target as any).x)
        .attr('y2', (d: any) => (d.target as any).y);

      g.selectAll<SVGGElement, any>('.node')
        .attr('transform', (d: any) => `translate(${(d as any).x},${(d as any).y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [filteredData, viewport, selectedNode, expandedNodes, hasChildren, isNodeExpanded, toggleNodeExpansion]);

  // 重置视图
  const handleResetView = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      const zoom = d3.zoom<SVGSVGElement, unknown>();
      svg.transition().duration(750).ease(d3.easeQuadOut).call(
        zoom.transform as any, 
        d3.zoomIdentity
      );
    }
  };

  // 放大视图 - 基于当前缩放级别
  const handleZoomIn = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      const zoom = d3.zoom<SVGSVGElement, unknown>();
      svg.transition().duration(300).ease(d3.easeQuadOut).call(
        zoom.scaleBy as any, 
        1.5
      );
    }
  };

  // 缩小视图 - 基于当前缩放级别
  const handleZoomOut = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      const zoom = d3.zoom<SVGSVGElement, unknown>();
      svg.transition().duration(300).ease(d3.easeQuadOut).call(
        zoom.scaleBy as any, 
        0.7
      );
    }
  };

  return (
    <div 
      ref={containerRef} 
      className="w-full h-full relative overflow-hidden transition-all duration-500"
      style={{ 
        minHeight: '400px',
        backgroundColor: '#f8fafc',
        borderRadius: '0.5rem'
      }}
    >
      {/* 知识图谱控制栏 - 自适应显示，优化小窗口布局 */}
      <div className={`absolute ${viewport.width >= 768 ? 'top-2 left-2' : 'bottom-2 left-2 right-2'} z-10 bg-white bg-opacity-95 p-2 rounded-lg shadow-md flex flex-wrap gap-2 text-sm transition-all duration-500 transform ${viewport.width < 768 ? 'translate-y-0' : ''} ${isAnimating ? 'opacity-80' : 'opacity-100'}`}>
        <button 
          className="flex-shrink-0 px-3 py-1.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all shadow-sm hover:shadow-md flex items-center justify-center"
          onClick={handleResetView}
          title="重置视图"
          style={{ 
            fontSize: viewport.width < 600 ? '10px' : '12px',
            minWidth: viewport.width < 400 ? '36px' : 'auto',
            paddingLeft: viewport.width < 400 ? '8px' : '12px',
            paddingRight: viewport.width < 400 ? '8px' : '12px'
          }}
          aria-label="重置视图"
        >
          <span className="mr-1">↺</span>
          {viewport.width >= 500 && '重置'}
        </button>
        <button 
          className="flex-shrink-0 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all shadow-sm flex items-center justify-center"
          onClick={handleZoomIn}
          title="放大"
          style={{ 
            fontSize: viewport.width < 600 ? '10px' : '12px',
            minWidth: viewport.width < 400 ? '36px' : 'auto',
            paddingLeft: viewport.width < 400 ? '8px' : '12px',
            paddingRight: viewport.width < 400 ? '8px' : '12px'
          }}
          aria-label="放大"
        >
          <span className="mr-1">+</span>
          {viewport.width >= 500 && '放大'}
        </button>
        <button 
          className="flex-shrink-0 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all shadow-sm flex items-center justify-center"
          onClick={handleZoomOut}
          title="缩小"
          style={{ 
            fontSize: viewport.width < 600 ? '10px' : '12px',
            minWidth: viewport.width < 400 ? '36px' : 'auto',
            paddingLeft: viewport.width < 400 ? '8px' : '12px',
            paddingRight: viewport.width < 400 ? '8px' : '12px'
          }}
          aria-label="缩小"
        >
          <span className="mr-1">-</span>
          {viewport.width >= 500 && '缩小'}
        </button>
        
        {/* 小窗口下隐藏部分控件，保持界面简洁 */}
        {viewport.width >= 768 && (
          <button 
            className="flex-shrink-0 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-all shadow-sm flex items-center justify-center"
            onClick={() => console.log('显示图例')}
            title="显示图例"
            style={{ fontSize: '12px' }}
            aria-label="显示图例"
          >
            <span className="mr-1">📊</span>
            图例
          </button>
        )}
        
        {viewport.width >= 1024 && (
          <button 
            className="flex-shrink-0 px-3 py-1.5 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-all shadow-sm flex items-center justify-center"
            onClick={() => console.log('导出图谱')}
            title="导出图谱"
            style={{ fontSize: '12px' }}
            aria-label="导出图谱"
          >
            <span className="mr-1">💾</span>
            导出
          </button>
        )}
      </div>
      
      {/* 主要知识图谱区域 - 优化滚动体验 */}
      <div className="w-full h-full overflow-auto" style={{ scrollBehavior: 'smooth' }}>
        <svg
          ref={svgRef}
          width={viewport.width}
          height={viewport.height}
          className="border border-gray-200 rounded-lg bg-gradient-to-br from-white to-gray-50 transition-all duration-500 shadow-sm"
          style={{ 
            cursor: 'grab',
            transform: 'translateZ(0)',
            willChange: 'transform',
          }}
        ></svg>
      </div>
      
      {/* 节点信息面板 - 自适应布局，优化小窗口显示 */}
      {selectedNode && (
        <div className={`absolute ${viewport.width >= 768 ? 'right-2 bottom-2' : 'bottom-20 left-2 right-2'} z-10 bg-white bg-opacity-98 p-3 rounded-lg shadow-lg transition-all duration-500 transform ${viewport.width < 768 ? 'translate-y-0' : ''} ${isAnimating ? 'opacity-80' : 'opacity-100'}`}>
          <div className="flex justify-between items-start">
            <h3 className="text-base font-semibold text-gray-800 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: 
                selectedNode.type === 'book' ? '#2c3e50' : 
                selectedNode.type === 'chapter' ? '#3498db' : 
                selectedNode.type === 'section' ? '#27ae60' : '#e74c3c' 
              }}></span>
              节点详情
            </h3>
            <button 
              className="text-gray-500 hover:text-gray-700 transition-colors p-1 rounded-full hover:bg-gray-100 flex items-center justify-center"
              onClick={() => setSelectedNode(null)}
              title="关闭"
              aria-label="关闭"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className={`mt-2 space-y-2 text-sm ${viewport.width < 768 ? 'max-h-52 overflow-y-auto pr-2' : ''}`}>
            <div className="grid grid-cols-12 gap-2">
              <div className="col-span-4 font-medium text-gray-600 whitespace-nowrap">ID:</div>
              <div className="col-span-8 text-gray-800 break-all truncate">{selectedNode.id}</div>
            </div>
            <div className="grid grid-cols-12 gap-2">
              <div className="col-span-4 font-medium text-gray-600 whitespace-nowrap">类型:</div>
              <div className="col-span-8">
                <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-xs capitalize">
                  {selectedNode.type}
                </span>
              </div>
            </div>
            <div className="grid grid-cols-12 gap-2">
              <div className="col-span-4 font-medium text-gray-600 whitespace-nowrap">标签:</div>
              <div className="col-span-8 text-gray-800 break-all">
                <span className="font-medium">{selectedNode.label}</span>
              </div>
            </div>
            {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
              <div className="grid grid-cols-12 gap-2">
                <div className="col-span-4 font-medium text-gray-600 whitespace-nowrap">元数据:</div>
                <div className="col-span-8">
                  <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto border border-gray-200 max-h-32">
                    {JSON.stringify(selectedNode.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* 悬停提示 - 智能显示，优化小窗口体验 */}
      {hoveredNode && viewport.width >= 600 && (
        <div className="fixed pointer-events-none z-20 p-2 bg-black bg-opacity-90 text-white text-xs rounded-lg shadow-lg transition-all duration-300 transform translate-y-1">
          <div className="font-medium truncate max-w-xs">{hoveredNode.label}</div>
          <div className="text-gray-300 capitalize">{hoveredNode.type}</div>
        </div>
      )}
      
      {/* 小窗口提示 - 帮助用户理解交互方式 */}
      {viewport.width < 600 && !selectedNode && (
        <div className="absolute top-2 left-2 right-2 z-10 bg-purple-50 border-l-4 border-purple-400 p-3 rounded-r-lg transition-all duration-500">
          <div className="text-sm text-purple-700 flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>您可以通过双指缩放或点击控制按钮来调整视图</span>
          </div>
        </div>
      )}
      
      {/* 空状态提示 - 优化视觉设计 */}
      {(!graph || !graph.nodes || graph.nodes.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 transition-all duration-500">
          <div className="text-center p-6 max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center">
              <svg className="h-8 w-8 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">暂无知识图谱数据</h3>
            <p className="text-gray-600 mb-4">请先上传PDF文件并构建知识图谱</p>
            <div className="text-xs text-gray-500">
              知识图谱将可视化展示文档中的实体关系和关键概念
            </div>
          </div>
        </div>
      )}
      
      {/* 加载状态指示器 */}
      {isBuilding && (
        <div className="absolute inset-0 z-30 bg-white bg-opacity-80 flex items-center justify-center transition-all duration-300">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-sm text-gray-600">构建知识图谱中...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraphVisualization;